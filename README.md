# bf_my_gcp_perms

Find which permissions the service account has access to

```bash
python3 bf_my_gcp_perms.py -h
usage: bf_my_gcp_perms.py [-h] -p PROJECT (-c CREDENTIALS | -t TOKEN)

Check the permissions of a service account

optional arguments:
  -h, --help            show this help message and exit
  -p PROJECT, --project PROJECT
                        Name of the project to use
  -c CREDENTIALS, --credentials CREDENTIALS
                        Path to credentials.json
  -t TOKEN, --token TOKEN
                        Raw access token

# Using json creds
python3 bf_my_gcp_perms.py -c /tmp/credentials.json -p project-name-1232

# Using raw token
python3 bf_my_gcp_perms.py -t <token> -p project-name-1232
```
