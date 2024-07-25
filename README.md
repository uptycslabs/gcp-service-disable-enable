# gcp-service-disable-enable
This script `gcp_service.py` can disable or enable all GCP services for all Projects under a given Folder. If disabled, Uptycs will no longer make GCP API calls to ingest CSPM object data for those services.   
The helper library `uptapy.py` is used to authenticate and make API calls. 

`Usage: python3 gcp_service.py -k <api_key_file> -a enable|disable -o <org_id> -f <folder>`\
`Usage: python3 gcp_service.py --keyfile <api_key_file> --action enable|disable --org_id <org_id> --folder <folder>`

You can download an <api_key_file> from the Uptycs console under: Configuration - Your_User 

The GCP `<org_id>` and `<folder>` are inputs to the script, along with an `<action>` of 'enable' or 'disable'. 

The script works by querying the Uptycs Global database for the GCP Projects belonging to the given 
org_id and folder using this SQL: 

   `select distinct p.project_id, f.display_name as folder_name
   from gcp_resourcemanager_project_current p, gcp_resourcemanager_folder_current f
   where p.org_id = f.org_id and f.name = p.parent and p.org_id = '<org_id>' 
   and f.display_name = '<folder>'`

The script then calls the API `GET /cloudAccounts` to get all integrated cloud accounts and loops thru them. 
If the cloud account is of type GCP and in the list created by the above SQL then it creates 'PUT suitable' JSON by removing 
certain JSON elements from the GET JSON. Removed elements include 'createdAt', 'id', 'updatedAt', 'customerId','deployerNode', etc.  
and sets status = 'enable' or 'disable' for all the services (depending on the input `<action>`).

Finally the script calls `PUT /cloudAccounts/<id> <cloud_acct_put_json>` to update each cloud account. 
