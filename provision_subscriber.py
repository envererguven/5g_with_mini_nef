import requests
import json

# Configuration
WEBUI_URL = "http://localhost:5000"
API_ROOT = f"{WEBUI_URL}/api"

# Sample Subscriber Data (Matching config/uecfg.yaml typically)
IMSI = "208930000000004"
MSISDN = "1234567891"  # The golden value we want to retrieve
OP_KEY = "8e27b6af487340f2ac63df" # Default Free5GC
KEY = "8baf473f2f8fd09487cccbd7097c6862"

def login():
    # Attempt login to internal API (if auth required, default often skips or use admin/free5gc)
    # Most Free5GC WebUI internal APIs might be open or use token.
    # We'll try posting directly to subscriber endpoint.
    pass

def provision_subscriber():
    print(f"Provisioning Subscriber {IMSI} with MSISDN {MSISDN}...")

    ue_data = {
        "plmnID": "20893",
        "ueId": f"imsi-{IMSI}",
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
                "opValue": "981d464c7c52eb6e5036234984ad0bcf" # Derived from OP often
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
                f"msisdn-{MSISDN}"
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

    # Free5GC WebUI API Endpoint to add subscriber
    url = f"{WEBUI_URL}/api/subscriber/imsi-{IMSI}/20893"
    
    try:
        # Note: This checks availability. In a real script we might need to authenticate first 
        # via POST /api/login {username: admin, password: free5gc} -> Token
        
        # Step 1: Login
        session = requests.Session()
        login_resp = session.post(f"{WEBUI_URL}/api/login", json={"username": "admin", "password": "free5gc"})
        if login_resp.status_code == 200:
             print("Login successful.")
             token = login_resp.json().get("token")
             headers = {"Authorization": f"Bearer {token}"}
        else:
             print("Login failed, trying without auth (older versions)...")
             headers = {}

        # Step 2: Post Data
        # Note: API structure varies by version. Using commonly observed payload.
        resp = session.post(url, json=ue_data, headers=headers)
        
        if resp.status_code in [200, 201]:
            print("✅ Subscriber provisioned successfully!")
        else:
            print(f"❌ Failed to provision: {resp.status_code} - {resp.text}")

    except Exception as e:
        print(f"❌ Error connecting to WebUI: {e}")
        print("Ensure 'free5gc-webui' container is running.")

if __name__ == "__main__":
    provision_subscriber()
