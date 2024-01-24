import argparse
import requests
import tqdm
import re
from bs4 import BeautifulSoup
from google.oauth2 import service_account
import google.oauth2.credentials
import googleapiclient.discovery
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from threading import Lock


def download_gcp_permissions():
    """Get list with all permissions og GCP (copied and modified from https://github.com/iann0036/iam-dataset/blob/main/gcp_get_permissions.py)"""

    base_ref_page = requests.get("https://cloud.google.com/iam/docs/permissions-reference").text
    frame_page_url = re.search('<iframe src="([^"]+)"', base_ref_page).group(1)
    if frame_page_url[0] == "/":
        frame_page_url = "https://cloud.google.com" + frame_page_url
    frame_page = requests.get(frame_page_url).text
    parsed_frame_page = BeautifulSoup(frame_page, features="lxml")

    results = []

    for row in parsed_frame_page.find('tbody').find_all('tr'):
        permission = row.find_all('td')[0].get('id')
        results.append(permission)

    return results

def check_permissions(perms, service, project, verbose):
    """Test if the user has the indicated permissions"""

    # Wait 1 second to avoid hitting the rate limit

    # Get the permissions for the current project
    req = service.projects().testIamPermissions(
        resource=project,
        body={"permissions": perms},
    )

    have_perms = []

    try:
        returnedPermissions = req.execute()
        have_perms = returnedPermissions.get("permissions", [])
    except googleapiclient.errors.HttpError as e: # Example error: <HttpError 400 when requesting https://cloudresourcemanager.googleapis.com/v1/projects/digital-bonfire-410512:testIamPermissions?alt=json returned "Permission policyremediatormanager.remediatorServices.enable is not valid for this resource.". Details: "Permission policyremediatormanager.remediatorServices.enable is not valid for this resource.">
        for perm in perms:
            if " "+perm+" " in str(e): #Add spaces to avoid problems
                perms.remove(perm)
                return check_permissions(perms, service, project, verbose)
        
    except Exception as e:
        print("Error:")
        print(e)
    
    if have_perms and verbose:
        print(f"Found: {have_perms}")
    
    return have_perms


def divide_chunks(l, n):
    """Divide a list in sublists of fixed number of elements"""
    for i in range(0, len(l), n):
        yield l[i:i + n]
 

def main():
    parser = argparse.ArgumentParser(description='Check the permissions of a service account')
    parser.add_argument('-p','--project', help='Name of the project to use', required=True)
    parser.add_argument('-v','--verbose', help='Print the found permissions as they are found', action='store_true')
    parser.add_argument('-T','--threads', help='Number of threads to use, be careful with rate limits. Default is 3.', default=3, type=int)
    parser.add_argument('-s','--services', help='Comma separated list of GCP service by its api names to check only (e.g. filtering top 10 services: -s iam.,compute.,storage.,container.,bigquery.,cloudfunctions.,pubsub.,sqladmin.,cloudkms.,secretmanager.). Default is all services.', default='', type=str)
    parser.add_argument('-S','--size', help='Size of the chunks to divide all the services into. Default is 50.)', default=50)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c','--credentials', help='Path to credentials.json')
    group.add_argument('-t','--token', help='Raw access token')
    args = vars(parser.parse_args())

    project = args['project']
    verbose = args['verbose']
    n_threads = int(args['threads'])
    services_grep = [s.strip() for s in args['services'].split(',')] if args['services'] else []
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
    list_perms.sort()

    print(f"Downloaded {len(list_perms)} GCP permissions")
    
    if len(services_grep)>0:
        # Filter only inte interesting services
        list_perms = [perm for perm in list_perms for grep_perm in services_grep if grep_perm.lower() in perm.lower()]
        print(f"Filtered to {len(list_perms)} GCP permissions")

    # Check permissions
    divided_list_perms = list(divide_chunks(list_perms, 20))
    have_perms = []
    have_perms_lock = Lock()  # Lock for thread-safe operations on have_perms

    def thread_function(subperms):
        # Create the service account client
        # Create 1 per thread to avoid errors!
        service = googleapiclient.discovery.build(
            "cloudresourcemanager", "v1", credentials=credentials
        )

        # Test the permissions
        perms = check_permissions(subperms, service, project, verbose)
        with have_perms_lock:  # Ensure thread-safe update of have_perms
            have_perms.extend(perms)

    # Setup ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=n_threads) as executor, tqdm.tqdm(total=len(divided_list_perms)) as progress:
        futures = {executor.submit(thread_function, subperms): subperms for subperms in divided_list_perms}
        for future in concurrent.futures.as_completed(futures):
            progress.update(1)  # Update tqdm progress for each completed thread

    print("[+] Your Permissions: \n- " + '\n- '.join(have_perms))
    print("")


if __name__ == "__main__":
    main()