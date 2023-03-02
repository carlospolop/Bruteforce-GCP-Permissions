import argparse
import requests
import json
import tqdm
import re
from bs4 import BeautifulSoup

from google.oauth2 import service_account
import google.oauth2.credentials
import googleapiclient.discovery
from time import sleep

def download_gcp_permissions():
    """Get list with all permissions og GCP (copied and modified from https://github.com/iann0036/iam-dataset/blob/main/gcp_get_permissions.py)"""

    base_ref_page = requests.get("https://cloud.google.com/iam/docs/permissions-reference").text
    frame_page_url = re.search('<iframe src="([^"]+)"', base_ref_page).group(1)
    if frame_page_url[0] == "/":
        frame_page_url = "https://cloud.google.com" + frame_page_url
    frame_page = requests.get(frame_page_url).text
    parsed_frame_page = BeautifulSoup(frame_page, features="lxml")

    result = []

    for row in parsed_frame_page.find('tbody').find_all('tr'):
        permission = row.find_all('td')[0].get('id')
        result.append(permission)

    return result

def check_permissions(perms, service, project):
    """Test if the user has the indicated permissions"""

    # Wait 1 second to avoid hitting the rate limit
    sleep(1)

    # Get the permissions for the current project
    req = service.projects().testIamPermissions(
        resource=project,
        body={"permissions": perms},
    )

    have_perms = []

    try:
        returnedPermissions = req.execute()
        have_perms = returnedPermissions.get("permissions", [])
    except googleapiclient.errors.HttpError as e:
        for perm in perms:
            if perm in str(e):
                perms.remove(perm)
                return check_permissions(perms, service, project)
        
    except Exception as e:
        print("Error:")
        print(e)
    
    if have_perms:
        print(f"Found: {have_perms}")
    
    return have_perms


def divide_chunks(l, n):
    """Divide a list in sublists of fixed number of elements"""
    for i in range(0, len(l), n):
        yield l[i:i + n]
 


def main():
    parser = argparse.ArgumentParser(description='Check the permissions of a service account')
    parser.add_argument('-p','--project', help='Name of the project to use', required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c','--credentials', help='Path to credentials.json')
    group.add_argument('-t','--token', help='Raw access token')
    args = vars(parser.parse_args())

    project = args['project']
    if args.get('token'):
        access_token = args['token']
        credentials = google.oauth2.credentials.Credentials(access_token.rstrip())
    else:
        credentials_path = args['credentials']
        # Create the service account credentials
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

    # Load permissions from permissions.json
    list_perms = list(set(download_gcp_permissions()))
    if list_perms is None or len(list_perms) == 0:
        print("Couldn't download the permissions")
        return

    print(f"Downloaded {len(list_perms)} GCP permissions")

    # Create the service account client
    service = googleapiclient.discovery.build(
        "cloudresourcemanager", "v1", credentials=credentials
    )

    divided_list_perms = list(divide_chunks(list_perms, 25))

    have_perms = []
    for subperms in tqdm.tqdm(divided_list_perms):
        # Test the permissions
        have_perms += check_permissions(subperms, service, project)

    print("[+] Your Permissions: \n- " + '\n- '.join(have_perms))
    print("")


if __name__ == "__main__":
    main()