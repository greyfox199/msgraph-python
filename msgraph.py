import msal
import requests
import sys, getopt
from os.path import exists
import json
import socket
from datetime import datetime
import logging


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

config = {}

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

validateJSONConfig("required", "client_id")
validateJSONConfig("required", "client_secret")
validateJSONConfig("required", "authority")

scope = "https://graph.microsoft.com/.default"
userData = []
record = {}

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


validateOptionalJSON("optional", "scope", scope)

def make_graph_caller(url, pagination=True):
    token_result = client.acquire_token_silent(config['scope'], account=None)

    #if token_result:
        #print('Access token was loaded from cache')

    if not token_result:
        token_result = client.acquire_token_for_client(scopes=config['scope'])
        #print('New access token aquired from AAD')

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


client = msal.ConfidentialClientApplication(config['client_id'], authority=config['authority'], client_credential=config['client_secret'])

##url = 'https://graph.microsoft.com/beta/reports/credentialUserRegistrationDetails'
#url = 'https://graph.microsoft.com/beta/reports/authenticationMethods/userRegistrationDetails'
#graph_data = make_graph_caller(url, pagination=True)

#print("############ MFA REG DETAILS #############")
#for data in graph_data:
#    print(data['userPrincipalName'])
#    print(data['isMfaRegistered'])

url = 'https://graph.microsoft.com/v1.0/users'
graph_data = make_graph_caller(url, pagination=True)

print("############ USERS #########")
for data in graph_data:
    print("-----------user------------")
    print("UPN: " + data['userPrincipalName'])
    print("display name: " + data['displayName'])
    #record.append({"userPrincipalName:" + data['userPrincipalName']})
    #record.append({"Id:" + data['Id']})
    #print(record)

    url = 'https://graph.microsoft.com/beta/users/' + data['userPrincipalName'] + '/authentication/methods'
    graph_sub_data = make_graph_caller(url, pagination=True)
    
    blnMFARegistered = False
    for sub_data in graph_sub_data:
        #print(sub_data)
        print("\t" + sub_data['@odata.type'])
        if sub_data['@odata.type'] == '#microsoft.graph.phoneAuthenticationMethod' or sub_data['@odata.type'] == '#microsoft.graph.fido2AuthenticationMethod' or sub_data['@odata.type'] == '#microsoft.graph.softwareOathAuthenticationMethod':
            blnMFARegistered = True
    if blnMFARegistered == True:
        print('\tMFA Registered Status: TRUE')
    else:
        print('\tMFA Registered Status: FALSE')

