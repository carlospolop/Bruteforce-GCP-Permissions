# bf_my_gcp_perms

Find which permissions a GCP principals has access to (you need to have credentials for it).

```bash
python3 bf_my_gcp_perms.py -h
usage: bf_my_gcp_perms.py [-h] -p PROJECT [-v] [-T THREADS] [-s SERVICES] [-S SIZE] (-c CREDENTIALS | -t TOKEN)

Check the permissions of a service account

options:
  -h, --help            show this help message and exit
  -p PROJECT, --project PROJECT
                        Name of the project to use
  -v, --verbose         Print the found permissions as they are found
  -T THREADS, --threads THREADS
                        Number of threads to use, be careful with rate limits. Default is 3.
  -s SERVICES, --services SERVICES
                        Comma separated list of GCP service by its api names to check only (e.g. filtering top 10 services: -s
                        iam.,compute.,storage.,container.,bigquery.,cloudfunctions.,pubsub.,sqladmin.,cloudkms.,secretmanager.). Default is all services.
  -S SIZE, --size SIZE  Size of the chunks to divide all the services into. Default is 50.)
  -c CREDENTIALS, --credentials CREDENTIALS
                        Path to credentials.json
  -t TOKEN, --token TOKEN
                        Raw access token


# Using json creds
python3 bf_my_gcp_perms.py -c /tmp/credentials.json -p project-name-1232

# Using raw token
python3 bf_my_gcp_perms.py -t <token> -p project-name-1232

# Using gcloud credentials
python3 bf_my_gcp_perms.py -v -p project-name-1232 -t $(gcloud auth print-access-token)

# Checking permissions only in the top10 services
python3 bf_my_gcp_perms.py -v -p project-name-1232 -t $(gcloud auth print-access-token) -s "iam.,compute.,storage.,container.,bigquery.,cloudfunctions.,pubsub.,sqladmin.,cloudkms.,secretmanager."
```
