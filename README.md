# msgraph-python
this utility is used to to get mfa data via the ms graph api endpoints from azure

Requirements:  
-Assumes an app registration has been created in Azure tenant with appropriate permissions and with a client secret created.  This will be used to actually make a connection to the MS graph api endpoints.   
-Assumes host path can run python scripts (has only been tested on linux/ubuntu)   
-Assumes the python3-pip OS package is installed   
-Assumes the msal python module has been installed   

# Azure configuration
This makes use of the MS graph api endpoints, and as such, an app registration must be created.  When creating a new registration, the only thing needed on the initial screen is a unique name.  Once it is created, the "Application (client) ID" can be obtained from the overview section.  
Once the client ID has been obtained, the following "API permissions" need to be added as "Application" type permissions:   
-User.Read.All   
-UserAuthenticationMethod.Read.All   
Once the permissions are added, someone with appropriate permissions (usually global admin) must grant admin consent for the requested permissions before they will be functional.   
A new client secret must also be created.  When creating a new client secret, choose an approriate expiration time and be sure to record the "value" for the "Secret ID" created when it is show, as this is the only time it will be shown.  If it is not saved, it must be deleted and a new one must be created.  The value for "Secret ID" will not be used.

# install
To install this script, either utilize the git-clone feature or manaually download from this repo.  It should be placed in a suitable location of your choosing for scheduled tasks.  This script requires a json config file to be passed in as a parameter.  The config file should be placed in an appropriate location; it does not have to reside in the same location as the script but it can.  This file WILL have the client secret in it (until I can find a better way around this), so ensure that only the user running it can read it:

chmod 600 msgraph.json

Once the python script and json config file have been created and configured, the script can be run manually as follows:  

python3 msgraph.py -c "/path/to/msgraph.json"

# config file
The config file is a json-formatted config file.  There are 3 required fields and one optional field to control functionality

The simplest file will be this:
```json
{
    "required": {
        "client_id": "[INSERT YOUR CLIENT ID]",
        "client_secret": "[INSERT YOUR CLIENT SECRET]",
        "authority": "https://login.microsoftonline.com/[INSERT YOUR TENANT ID]",
        "pathToExportFilesDir": "/path/to/exportfiles/dir"
    }
}
```
**client_id**: This is the "Application (client) ID" from the azure app registration created for the graph api.  
**client_secret**: This is the "Value" for the "Secret ID" created under "client secrets" for the app registration created for the graph api.   
**authority**:  This is the login.microsoft.com url appended with your "Directory (tenant) ID" from your Azure tenant.   
**pathToExportFilesDir**: This is the path that will be used to write the exported json and csv files for the mfa report

The complete list of optional parameters is as follows:  

```json
{
    "required": {
       "client_id": "[INSERT YOUR CLIENT ID]",
        "client_secret": "[INSERT YOUR CLIENT SECRET]",
        "authority": "https://login.microsoftonline.com/[INSERT YOUR TENANT ID]",
        "pathToExportFilesDir": "/path/to/exportfiles/dir"
    },
    "optional": {
        "scope": "https://graph.microsoft.com/.default"
    }
}
```

**scope**: This is a scope that entails what permissions will be used when using the ms graph api endpoints.  If a value is not provided, "https://graph.microsoft.com/.default" will be used as a default value, which should suffice in most cases.   

# output
This will create two files, a json-formatted file and a csv file.  

the json-formatted file will have a name of msgraph-export.json in the specified pathToExportFilesDir config entry.  It will have the following structure:

```json
[
    {
        "userPrincipalName": "upn@domain.name",
        "id": "[id of azure user object]",
        "phoneAuthenticationMethod": "[TRUE | FALSE]",
        "fido2AuthenticationMethod": "[TRUE | FALSE]",
        "softwareOathAuthenticationMethod": "[TRUE | FALSE]",
        "microsoftAuthenticatorAuthenticationMethod": "[TRUE | FALSE]",
        "mfaRegistered": "[TRUE | FALSE]"
    }
]
```json

the csv file will have a name of msgraph-export.csv in the specified pathToExportFilesDir config entry.  It willl have the following structure:

userPrincipalName,id,phoneAuthenticationMethod,fido2AuthenticationMethod,softwareOathAuthenticationMethod,microsoftAuthenticatorAuthenticationMethod,mfaRegistered
upn@domain.name,[id of azure user object],[TRUE | FALSE],[TRUE | FALSE],[TRUE | FALSE],[TRUE | FALSE],[TRUE | FALSE]

The following keys/columns will contain TRUE or FALSE depending on whether the user has registered the method in question:
-phoneAuthenticationMethod   
-fido2AuthenticationMethod   
-softwareOathAuthenticationMethod   
-microsoftAuthenticatorAuthenticationMethod   

The key/column of mfaRegistered will have a value of TRUE if any of the methods listed above are set by the user, and will have a value of FALSE if none of the methods listed have been registered.