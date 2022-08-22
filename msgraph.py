import msal
import requests
import sys, getopt
from os.path import exists
import json
import socket
from datetime import datetime
import logging
import csv


argumentList = sys.argv[1:]
 
# Options
options = "hc:"
ConfigFilePath = ""
long_options = ["Help", "ConfigFilePath"]

#get command line arguments
try:
    # Parsing argument
    arguments, values = getopt.getopt(argumentList, options, long_options)

    if arguments:
        for currentArgument, currentValue in arguments:
            if currentArgument in ("-h", "--Help"):
                print ("Usage: python3 msgraph.py -c /path/to/config.json")
             
            elif currentArgument in ("-c", "--ConfigFilePath"):
                ConfigFilePath = currentValue
    else:
        print("Usage: python3 msgraph.py -c /path/to/config.json")
        exit()
             
except getopt.error as err:
    # output error, and return with an error code
    print(str(err))

#we require a json config file, so if it doesn't exist, abort
if not exists(ConfigFilePath):
    print("json config file specified at " + ConfigFilePath + " does not exist, aborting process")
    exit()

#open config file and check that it's a valid json file, if its not, abort
objConfigFile = open (ConfigFilePath, "r")
try:
    jsonData = json.loads(objConfigFile.read())
except Exception as e:
    print("Config file of " + ConfigFilePath + " is not a valid json file, aborting process")
    exit()

#create config dictionary object to hold configuration items
config = {}

#function to do general validation on json configuration items
def validateJSONConfig(section, key):
    if key in jsonData[section]:
        try:
            config.update({key:str(jsonData[section][key])})
        except:
            print("required field of " + key + " in config not valid, aborting proces")
            exit()
    else:
        print("required field of " + key + " in config does not exist, aborting proces")
        exit()

#validate all required keys in config file
validateJSONConfig("required", "client_id")
validateJSONConfig("required", "client_secret")
validateJSONConfig("required", "authority")
validateJSONConfig("required", "pathToExportFilesDir")

#since pathToExportFilesDir is a local path, validate that it exists before proceeding
if not exists(config["pathToExportFilesDir"]):
    print("local path of " + config["pathToExportFilesDir"] + "does not exist, aborting process")
    exit()

#set up variables for use later in script globally
scope = "https://graph.microsoft.com/.default"
userData = []
record = {}

#validate optoinal json data, if it doesn't exist, use default value passed in
def validateOptionalJSON(section, key, default):
    if key in jsonData[section]:
        try:
            config.update({key:[str(jsonData[section][key])]})
        except:
            print("failed to load " + key + " using default")
            config.update({key:[default]})
    else:
        print(key + " not present in config, using default")
        config.update({key:[default]})

#validate optional configuration items
validateOptionalJSON("optional", "scope", scope)

#function to make api call to ms graph, doing pagination if required
def getGraphData(url, pagination=True):
    token_result = client.acquire_token_silent(config['scope'], account=None)

    if not token_result:
        token_result = client.acquire_token_for_client(scopes=config['scope'])

    if 'access_token' in token_result:
        headers = {'Authorization': 'Bearer ' + token_result['access_token']}
        graph_results = []
        
        while url:
            try:
                graph_result = requests.get(url=url, headers=headers).json()
                graph_results.extend(graph_result['value'])
                if (pagination == True):
                    url = graph_result['@odata.nextLink']
                else:
                    url = None
            except:
                break
    else:
        print(token_result.get('error'))
        print(token_result.get('error_description'))
        print(token_result.get('correlation'))

    return graph_results

#authenticate to ms graph using data from configuration file
client = msal.ConfidentialClientApplication(config['client_id'], authority=config['authority'], client_credential=config['client_secret'])

#attempt to query all users via users graph endpoint
url = 'https://graph.microsoft.com/beta/users'
graph_data = getGraphData(url, pagination=True)
for data in graph_data:

    #initiallize record dictionary per user and start populating it with data per user
    record = {}
    record["userPrincipalName"] = data['userPrincipalName']
    record["id"] = data['id']

    #now that we have data per user, call graph endpoint to get authentication method details
    url = 'https://graph.microsoft.com/beta/users/' + data['userPrincipalName'] + '/authentication/methods'
    graph_sub_data = getGraphData(url, pagination=True)

    #initialize some variables per user before processing authentication methods data
    blnMFARegistered = False

    record["phoneAuthenticationMethod"] = "FALSE"
    record["fido2AuthenticationMethod"] = "FALSE"
    record["softwareOathAuthenticationMethod"] = "FALSE"
    record["microsoftAuthenticatorAuthenticationMethod"] = "FALSE"

    #loop through each authentication method and store values
    for sub_data in graph_sub_data:
        if sub_data['@odata.type'] == '#microsoft.graph.phoneAuthenticationMethod' or sub_data['@odata.type'] == '#microsoft.graph.fido2AuthenticationMethod' or sub_data['@odata.type'] == '#microsoft.graph.softwareOathAuthenticationMethod' or sub_data['@odata.type'] == '#microsoft.graph.microsoftAuthenticatorAuthenticationMethod':
            blnMFARegistered = True

        if sub_data['@odata.type'] == '#microsoft.graph.phoneAuthenticationMethod':
            record["phoneAuthenticationMethod"] = "TRUE"

        if sub_data['@odata.type'] == '#microsoft.graph.fido2AuthenticationMethod':
            record["fido2AuthenticationMethod"] = "TRUE"

        if sub_data['@odata.type'] == '#microsoft.graph.softwareOathAuthenticationMethod':
            record["softwareOathAuthenticationMethod"] = "TRUE"

        if sub_data['@odata.type'] == '#microsoft.graph.microsoftAuthenticatorAuthenticationMethod':
            record["microsoftAuthenticatorAuthenticationMethod"] = "TRUE"

    if blnMFARegistered == True:
        record["mfaRegistered"] = "TRUE"
    else:
        record["mfaRegistered"] = "FALSE"

    #append user data to array for later processing
    userData.append(record)


#now that we have all our user data in an array, export it to both json and csv file
#export user data to json file using path from config file
with open(str(config["pathToExportFilesDir"]) + "/msgraph-export.json", "w") as json_file:
    json.dump(userData, json_file, indent=4)

#export user data to csv file using path from config file
with open(str(config["pathToExportFilesDir"]) + "/msgraph-export.csv", 'w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["userPrincipalName", "id", "phoneAuthenticationMethod", "fido2AuthenticationMethod", "softwareOathAuthenticationMethod", "microsoftAuthenticatorAuthenticationMethod", "mfaRegistered"])
    for item in userData:
        writer.writerow([item["userPrincipalName"], item["id"], item["phoneAuthenticationMethod"], item["fido2AuthenticationMethod"], item["softwareOathAuthenticationMethod"], item["microsoftAuthenticatorAuthenticationMethod"], item["mfaRegistered"]])

print("JSON file available at " + str(config["pathToExportFilesDir"]) + "/msgraph-export.json")
print("CSV file available at " + str(config["pathToExportFilesDir"]) + "/msgraph-export.csv")