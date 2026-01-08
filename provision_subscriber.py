import requests
import json
import time

# Configuration
WEBUI_URL = "http://localhost:5000"
API_ROOT = f"{WEBUI_URL}/api"

OP_KEY = "8e27b6af487340f2ac63df" # Default Free5GC
KEY = "8baf473f2f8fd09487cccbd7097c6862"

SUBSCRIBERS = [
    {"imsi": "208930000000003", "msisdn": "1234567891", "name": "UE1"},
    {"imsi": "208930000000004", "msisdn": "1234567892", "name": "UE2"}
]

def login():
    session = requests.Session()
    try:
        login_resp = session.post(f"{WEBUI_URL}/api/login", json={"username": "admin", "password": "free5gc"})
        if login_resp.status_code == 200:
             print("Login successful.")
             token = login_resp.json().get("token")
             return session, {"Authorization": f"Bearer {token}"}
    except Exception:
        pass
    print("Login failed or not needed, trying without auth...")
    return session, {}

def provision_subscriber(session, headers, sub):
    imsi = sub['imsi']
    msisdn = sub['msisdn']
    name = sub['name']
    
    print(f"[{name}] Provisioning IMSI {imsi} (MSISDN {msisdn})...")

    ue_data = {
        "plmnID": "20893",
        "ueId": f"imsi-{imsi}",
        "AuthenticationSubscription": {
            "authenticationManagementField": "8000",
            "authenticationMethod": "5G_AKA",
            "milenage": {
                "op": {
                    "encryptionAlgorithm": 0,
                    "encryptionKey": 0,
                    "opValue": ""
                }
            },
            "opc": {
                "encryptionAlgorithm": 0,
                "encryptionKey": 0,
                "opValue": "981d464c7c52eb6e5036234984ad0bcf" 
            },
            "permanentKey": {
                "encryptionAlgorithm": 0,
                "encryptionKey": 0,
                "permanentKeyValue": KEY
            },
            "sequenceNumber": "16f3b3f70fc2"
        },
        "AccessAndMobilitySubscriptionData": {
            "gpsis": [
                f"msisdn-{msisdn}"
            ],
            "nssai": {
                "defaultSingleNssais": [
                    { "sd": "010203", "sst": 1 }
                ],
                "singleNssais": [
                    { "sd": "010203", "sst": 1 }
                ]
            },
            "subscribedUeAmbr": {
                "downlink": "1 Gbps",
                "uplink": "200 Mbps"
            }
        },
        "SessionManagementSubscriptionData": [
            {
                "singleNssai": { "sd": "010203", "sst": 1 },
                "dnnConfigurations": {
                    "internet": {
                        "pduSessionTypes": { "defaultSessionType": "IPV4" },
                        "sscModes": { "defaultSscMode": "SSC_MODE_1" },
                        "5gQosProfile": {
                            "5qi": 9,
                            "arp": { "priorityLevel": 8 }
                        },
                        "sessionAmbr": {
                            "downlink": "1 Gbps",
                            "uplink": "200 Mbps"
                        }
                    }
                }
            }
        ]
    }

    url = f"{WEBUI_URL}/api/subscriber/imsi-{imsi}/20893"
    
    try:
        resp = session.post(url, json=ue_data, headers=headers)
        if resp.status_code in [200, 201]:
            print(f"[OK] {name} provisioned successfully!")
        elif resp.status_code == 401:
             print(f"[INFO] 401 Unauthorized. Retrying without auth header...")
             resp = session.post(url, json=ue_data) # Try without headers
             if resp.status_code in [200, 201]:
                 print(f"[OK] {name} provisioned (no-auth).")
             else:
                 print(f"[FAIL] Retry failed: {resp.status_code} - {resp.text}")
        else:
            # If 409 conflict (already exists), we can try PUT or just ignore
            if resp.status_code == 409 or "exist" in resp.text:
                 # Try PUT to update
                 print(f"[INFO] {name} exists. Updating...")
                 resp = session.put(url, json=ue_data, headers=headers)
                 if resp.status_code in [200, 204]:
                     print(f"[OK] {name} updated.")
                 else:
                     print(f"[FAIL] Failed to update {name}: {resp.status_code}")
            else:
                print(f"[FAIL] Failed to provision {name}: {resp.status_code} - {resp.text}")

    except Exception as e:
        print(f"[FAIL] Error connecting to WebUI: {e}")

if __name__ == "__main__":
    session, headers = login()
    for sub in SUBSCRIBERS:
        provision_subscriber(session, headers, sub)
        time.sleep(1)
