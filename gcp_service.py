"""
gcp_service.py
This script enables or disables Uptycs ingestion for all GCP services in all projects under a folder.
Note if new JSON elements are added by Uptycs to the 'GET cloudAccounts' JSON then we may need to
add to the exclude_list in remove_elements().

Author: jwayte@uptycs.com
Date:   2024-07-19
"""

import sys
import json
import uptapi
import warnings
warnings.filterwarnings("ignore")

def remove_elements(input_json):
    """ Copies the input_json (returned from GET API call) but skips certain elements such as:
            "createdAt": "2024-07-12T08:26:41.721Z"
            "id": "8961da24-c31a-4d42-9dce-b00dba9015f4"
        This is so the resulting output_json can be used in 'PUT /cloudAccounts/{cloudAccountId}'
    """
    output_json = {}
    list1 = ['createdAt', 'id', 'updatedAt', 'customerId','deployerNode','organizationUnitId','organizationId','tenantGroupId','deploymentStatus']
    list2 = ['publishReadOnlyEvents', 'ingestDataEvents', 'integrationType', 'batchId', 'sideQueryIntegrations','sideQueryIntegrationsSummary', 'links']
    exclude_list = list1 + list2
    for k in input_json.keys():
        if k not in exclude_list:
            output_json[k] = input_json[k]
    return output_json

def set_service_status(input_json, action):
    """ If action = enable  then sets status: active   for all cloudServices in the input JSON
        If action = disable then sets status: inactive for all cloudServices in the input JSON
    """
    status = ''
    if action == 'enable':
        status = 'active'
    elif action == 'disable':
        status = 'inactive'
    else:
        print('Error! action argument for set_service_status must be "enable" or "disable"')
        exit(1)
    # create a new list of cloud services (where we can set their status)
    cloud_services = []
    # copy the input cloud services and set their status
    for service in input_json['cloudServices']:
        service.update({'status':status})
        cloud_services.append(service)
    output_json = input_json
    # delete existing services with their old status
    del output_json['cloudServices']
    # add the new cloud services array (with the new statuses)
    output_json['cloudServices'] = cloud_services
    return output_json

# arguments
api_key_file = ''
org = ''
folder = ''
action = ''
for i in range(1, len(sys.argv)):
    if sys.argv[i] == '--keyfile' or sys.argv[i] == '-k':
        api_key_file = sys.argv[i+1]
    if sys.argv[i] == '--org_id' or sys.argv[i] == '-o':
        org = sys.argv[i+1]
    if sys.argv[i] == '--folder' or sys.argv[i] == '-f':
        folder = sys.argv[i+1]
    elif sys.argv[i] == '--action' or sys.argv[i] == '-a':
        action = sys.argv[i + 1]

if (not api_key_file or not org or not folder) or action not in ('enable', 'disable'):
    print('Usage: gcp_service.py -k <api_key_file> -a enable|disable -o <org_id> -f <folder>')
    print('Or:    gcp_service.py --keyfile <api_key_file> --action enable|disable --org_id <org_id> --folder <folder>')
    sys.exit(1)
else:
    print('Processing GCP projects in org_id: %s and folder: %s' % (org, folder))

# get the API auth token
auth = uptapi.UptApiAuth(api_key_file)

# Define SQL for Uptycs global query for list of GCP projects in the Org, under that Folder
sql = """select distinct p.project_id, f.display_name as folder_name
         from gcp_resourcemanager_project_current p, gcp_resourcemanager_folder_current f
         where p.org_id = f.org_id and f.name = p.parent and p.org_id = '"""
sql = sql + org + "' and f.display_name = '"
sql = sql + folder + "'"

# run the SQL
projects = uptapi.UptQueryGlobal(auth, sql)
# put the resulting row values (project_id's) into a list
project_list = []
for row in projects.response_json['items']:
    project_list.append(row['project_id'])

# get all the cloud accounts (AWS, GCP, Azure)
cloud_accounts = uptapi.UptApiCall(auth, '/cloudAccounts', 'GET', {})

# loop through all the cloud accounts
for ca in cloud_accounts.response_json['items']:
    # only accept GCP accounts in the project_list (under that folder)
    if ca['connectorType'] == 'gcp' and ca['tenantId'] in project_list:
        # call function to remove unwanted JSON elements (from GET JSON), ready for PUT
        ca_for_put = remove_elements(ca)

        # call function to set the services as active or inactive in the JSON
        ca_for_put = set_service_status(ca_for_put, action)

        # update the cloudAccount status for all the services by calling the PUT API with the new JSON
        print('Running %s of services for Project: %s' % (action, ca['tenantName']))
        try:
            cloud_account_put_result = uptapi.UptApiCall(auth, '/cloudAccounts/'+ca['id'], 'PUT', ca_for_put)
        except:
            print('Error calling API %s' % '/cloudAccounts/'+ca['id'])
            exit(1)

print('Processing complete, have a nice day.')

