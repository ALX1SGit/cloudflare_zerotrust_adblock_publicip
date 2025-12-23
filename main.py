#/usr/bin/python
# Script designed to perform Cloudflare Zero Trust updates
# Created By AC - 0.1 - 20251222

import requests
import httpx
from requests.structures import CaseInsensitiveDict
import pandas
import json
from datetime import datetime
import traceback

# ACCOUNT INFORMATION HERE
name_account = 'home' #Also location name
email_account = ''
token = "Bearer 

# DO NOT TOUCH THIS PART
url = "https://api.cloudflare.com/client/v4/user/tokens/verify"
ads_list = "https://small.oisd.nl/"
ads_fw_name = "Adblock-Plus" # Also name for filtering lists

headers = CaseInsensitiveDict()
headers["X-Auth-Email"] = email_account
headers["Authorization"] = token
headers["Content-Type"] = "application/json"

def get_dnslocations(headers, accountid):
    query = "https://api.cloudflare.com/client/v4/accounts/" + accountid + "/gateway/locations"
    print(query)
    resp = httpx.get(query, headers=headers, verify=False)
    #print(resp.text)
    return resp.json().get('result')

def get_dnsfirewall(headers, accountid):
    query = "https://api.cloudflare.com/client/v4/accounts/" + accountid + "/gateway/rules"
    print(query)
    resp = httpx.get(query, headers=headers, verify=False)
    print(resp.text)
    return resp.json().get('result')

def get_lists(accountid):
    query = "https://api.cloudflare.com/client/v4/accounts/" + accountid + "/gateway/lists"
    print(query)
    resp = httpx.get(query, headers=headers, verify=False)
    print(resp.text)
    return resp.json().get('result')

def get_list_content(accountid, listid):
    query = "https://api.cloudflare.com/client/v4/accounts/" + accountid + "/gateway/lists/" + listid
    print(query)
    resp = httpx.get(query, headers=headers, verify=False)
    print(resp.text)
    return resp.json().get('result')

def return_id_for_account(account_name):
    '''return account for a name'''
    headers2 = CaseInsensitiveDict()
    query = "https://api.cloudflare.com/client/v4/accounts"
    headers2["X-Auth-Email"] = email_account
    headers2["Authorization"] = token
    headers2["Content-Type"] = "application/json"
    resp = requests.get(query, headers=headers2).json()
    print(resp)
    for i in resp.get('result'):
        if i.get('name') == account_name:
            return i.get('id')

def get_public_ip():
    query = "https://myip.dnsomatic.com/"
    resp = httpx.get(query, verify=False)
    if "." in resp.text:
        return resp.text
    else:
        return False

def create_location(headers, accountid, location_name, public_ip):
    new_location = {
        "name": location_name,
        "networks": [
            {
                "network": public_ip
            }
        ],
        'client_default': True,
        "ecs_support": True,
    }
    query = "https://api.cloudflare.com/client/v4/accounts/" + accountid + "/gateway/locations"
    resp = httpx.post(query, data=json.dumps(new_location), headers=headers, verify=False)
    return resp.json().get('result')

def create_fw_rule(headers, accountid, rule_name, traffic):
    new_rule = {
      "name": rule_name,
      "description": "TEST",
      "enabled": True,
      "action": "block",
      "filters": [
        "dns"
      ],
      "traffic": traffic,
      "identity": "",
      "device_posture": "",
      "version": 4,
      "rule_settings": {},
      "sharable": True
    }
    query = "https://api.cloudflare.com/client/v4/accounts/" + accountid + "/gateway/rules"
    resp = httpx.post(query, data=json.dumps(new_rule), headers=headers, verify=False, timeout=300)
    print(resp)
    print(resp.text)
    return resp.json().get('result')

def create_list(headers, accountid, list_name, filter_list):
    data = {
        "name": list_name,
        "description": f"Updated: {datetime.now().date()}",
        "type": "DOMAIN",
        "items": filter_list
    }
    query = "https://api.cloudflare.com/client/v4/accounts/" + accountid + "/gateway/lists/"
    resp = httpx.post(query, data=json.dumps(data), headers=headers, verify=False, timeout=300)
    print(resp)
    #print(resp.text)
    return resp.json().get('result')

def update_list(headers, accountid, listid, filter_list):
    data = {
        "id": "c3747d25-4d4e-49b8-9dc2-919a0c397545",
        "name": ads_fw_name,
        "description": f"Updated: {datetime.now().date()}",
        "type": "DOMAIN",
        "items": filter_list
    }
    query = "https://api.cloudflare.com/client/v4/accounts/" + accountid + "/gateway/lists/" + listid
    resp = httpx.put(query, data=json.dumps(data), headers=headers, verify=False, timeout=300)
    print(resp)
    print(resp.text)
    return resp.json().get('result')

def remove_location(headers, accountid, locationid):
    query = "https://api.cloudflare.com/client/v4/accounts/" + accountid + "/gateway/locations/" + locationid
    resp = httpx.delete(query, headers=headers, verify=False)
    print(resp)
    #print(resp.text)
    return resp.json().get('result')

def remove_rule(headers, accountid, ruleid):
    query = "https://api.cloudflare.com/client/v4/accounts/" + accountid + "/gateway/rules/" + ruleid
    resp = httpx.delete(query, headers=headers, verify=False)
    print(resp)
    #print(resp.text)
    return resp.json().get('result')

def remove_list(headers, accountid, listid):
    query = "https://api.cloudflare.com/client/v4/accounts/" + accountid + "/gateway/lists/" + listid
    resp = httpx.delete(query, headers=headers, verify=False)
    print(resp)
    #print(resp.text)
    return resp.json().get('result')

def update_ip_location(accountid):
    # Get public IP
    public_ip = get_public_ip()
    public_ip = public_ip + "/32"

    # Get locations from CF
    cfgateway_locations_df = pandas.json_normalize(get_dnslocations(headers, accountid))

    # Check if the IP hs changed
    cf_location_ip = cfgateway_locations_df['networks'][0][0]['network']

    print(f"Public IP: {public_ip}")
    print(f"Cloudflare registered Public IP: {cf_location_ip}")

    if public_ip == cf_location_ip and public_ip != False:
        # Create the new default location with the newer IP
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        location_name = f"Canihouse_upd_{timestamp}"
        reply = create_location(headers, accountid, location_name, public_ip)
        # Remove the previous location with old IP
        old_location_name = cfgateway_locations_df['name'][0]
        print(f"Removing Old location: {old_location_name}")
        new_cfgateway_locations = get_dnslocations(headers, accountid)
        for elem in new_cfgateway_locations:
            if elem['name'] == old_location_name:
                old_location_id = elem['id']
        remove_location(headers, accountid, old_location_id)
    else:
        print("NO IP changes needed")

def load_oisd(url: str) -> str:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.text
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return ""

def update_ads_filter_rule(accountid):
    # Get id from Firewall adguard or create
    cfgateway_fw = get_dnsfirewall(headers, accountid)
    rule_id_list = list()
    rule_old_name_list = list()
    for rule in cfgateway_fw:
        if ads_fw_name in rule['name']:
            #rule_id = rule['id']
            #rule_old_name = rule['name']
            updated_at = rule['updated_at']
            rule_id_list.append(rule['id'])
            rule_old_name_list.append(rule['name'])
            break

    #if str(datetime.now().date()) in updated_at:
    if 1 == 2:
        print("Not update is needed")
    else:
        if len(rule_id_list) > 0:
            print("Policy needs to be updated")
            action = "UPDATE"

        else:
            print("Policy needs to be created")
            action = "CREATE"

        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        new_rule_name = f"{ads_fw_name}_upd_{timestamp}"
        #traffic = 'dns.fqdn == \"test1.com\" or dns.fqdn == \"test2.com\"'
        reply = create_fw_rule(headers, accountid, new_rule_name, traffic)
        print(reply)
        input("SERVICE STOP")
        if action == "UPDATE":
            print("Removing old rule")
            cfgateway_fw = get_dnsfirewall(headers, accountid)
            for rule in cfgateway_fw:
                if rule['name'] in str(rule_old_name_list):
                    old_rule_id = rule['id']
                    reply = remove_rule(headers, accountid, old_rule_id)
                    print(reply)

def update_ads_filter_list(accountid):
    # Reading latest version of adblock
    # ads_block_input = list(open("cloudflare_home_test.txt"))
    ads_block_input = load_oisd(ads_list)

    # Get id from Firewall adguard or create
    cfgateway_fw = get_dnsfirewall(headers, accountid)
    old_cf_fw_id = ""
    old_cf_lists_id = ""
    new_cf_fw_id = ""
    updated_at = ""
    new_cf_lists_id = list()
    for rule in cfgateway_fw:
        if ads_fw_name in rule['name']:
            old_cf_fw_id = rule['id']
            old_cf_lists_id = rule['traffic']
            updated_at = rule['updated_at']
    old_cf_lists_id = old_cf_lists_id.replace(" or ","").split("dns.fqdn in $")
    old_cf_lists_id.pop(0)

    if str(datetime.now().date()) not in updated_at and len(ads_block_input) > 1000:
    #if 1 == 1:
        if old_cf_fw_id != "":
            # Removing old Rule
            remove_rule(headers, accountid, old_cf_fw_id)

            # Removing old lists
            for listid in old_cf_lists_id:
                remove_list(headers, accountid, listid)

        filter_list = list()
        i = 0
        j = 0
        #for line in ads_block_input:
        for line in ads_block_input.splitlines():
            i = i + 1
            if i < 999:
                line = line.strip()
                if "||" in line and "^" in line:
                    line = line.replace("||", "").replace("^", "")
                    data = {
                        "value": line,
                    }
                    filter_list.append(data)
            else:
                j = j + 1
                i = 0
                if j < 10:
                    list_name = f"{ads_fw_name}-0{j}"
                else:
                    list_name = f"{ads_fw_name}-{j}"
                print(f"Creating list {list_name}")
                reply = create_list(headers, accountid, list_name, filter_list)
                new_cf_lists_id.append(reply['id'])
                filter_list = list()
        j = j + 1
        list_name = f"{ads_fw_name}-{j}"
        reply = create_list(headers, accountid, list_name, filter_list)
        new_cf_lists_id.append(reply['id'])
        traffic = f"dns.fqdn in ${new_cf_lists_id[0]}"
        for k in range(1,len(new_cf_lists_id)):
            traffic = traffic + " or dns.fqdn in $" + new_cf_lists_id[k]
        create_fw_rule(headers, accountid, ads_fw_name, traffic)

def remove_all_lists(accountid):
    reply = get_lists(accountid)
    print(reply)
    for elem in reply:
        listid = elem['id']
        remove_list(headers, accountid, listid)


try:
    accountid = return_id_for_account(name_account)
    update_ip_location(accountid)
    update_ads_filter_list(accountid)

    # Run this if there was a mistake only...
    #remove_all_lists(accountid)

except:
    print("Error during update")
    error = traceback.format_exc()
    print(error)
