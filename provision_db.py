import pymongo
import time

# Configuration
MONGO_URI = "mongodb://db:27017/"
DB_NAME = "free5gc"
COLLECTION = "subscriptionData.provisionedData.smData"

# We actually need to populate multiple collections for a full subscription:
# 1. subscriptionData.authenticationData.authenticationSubscription
# 2. subscriptionData.provisionedData.smData
# 3. subscriptionData.provisionedData.amData
# 4. policyData.ues.amData (optional but good)
# 5. policyData.ues.smData (optional)

# However, Free5GC structure is complex. 
# Simplest fallback: The WebUI failed, but maybe we can fix the WebUI request? 
# No, let's try direct DB. 

# Actually, the 'provision_subscriber.py' payload was roughly correct for the API.
# Mapping that to Mongo documents is tedious.

# Alternative: Use the 'provision_subscriber.py' but fix the Auth?
# Maybe the username/password is different?
# default is usually admin/free5gc.

# Let's try to debug the WebUI response first? 
# No, 401 is clear.

# Let's try one more thing: The 'mini-nef' app has a function `get_supi_from_mongo`.
# It assumes data is there.

# Let's use a known working "Direct DB Provisioning" script for Free5GC.
# It usually requires inserting into 'subscriptionData.authenticationData.authenticationSubscription', 'subscriptionData.provisionedData.amData', 'subscriptionData.provisionedData.smData'.

def get_auth_subs_data(imsi, opc, key, seq="16f3b3f70fc2"):
    return {
        "ueId": f"imsi-{imsi}",
        "authenticationMethod": "5G_AKA",
        "encPermanentKey": key,
        "protectionParameterId": "notConfigured",
        "sequenceNumber": {"sqn": seq, "sqnScheme": "NON_TIME_BASED", "lastIndexes": {"ausf": 0}},
        "authenticationManagementField": "8000",
        "algorithmId": "milenage",
        "encOpcKey": opc,
        "encTopcKey": None,
        "vectorGenerationInHss": False,
        "n5gcAuthMethod": "5G_AKA",
        "rgAuthenticationInd": False,
        "supi": f"imsi-{imsi}"
    }

def get_am_data(imsi, msisdn):
    return {
        "ueId": f"imsi-{imsi}",
        "servingPlmnId": "20893",
        "gpsis": [f"msisdn-{msisdn}"],
        "nssai": {
            "defaultSingleNssais": [{"sst": 1, "sd": "010203"}],
            "singleNssais": [{"sst": 1, "sd": "010203"}]
        },
        "subscribedUeAmbr": {"uplink": "200 Mbps", "downlink": "1 Gbps"},
        "subscribedDnnList": ["internet"]
    }

def get_sm_data(imsi):
    return {
        "ueId": f"imsi-{imsi}",
        "servingPlmnId": "20893",
        "singleNssai": {"sst": 1, "sd": "010203"},
        "dnnConfigurations": {
            "internet": {
                "pduSessionTypes": {"defaultSessionType": "IPV4", "allowedSessionTypes": ["IPV4"]},
                "internal_Group_Id": "Group-1",
                "sscModes": {"defaultSscMode": "SSC_MODE_1", "allowedSscModes": ["SSC_MODE_1"]},
                "5gQosProfile": {"5qi": 9, "arp": {"priorityLevel": 8, "preemptCap": "NOT_PREEMPT", "preemptVuln": "NOT_PREEMPTABLE"}, "priorityLevel": 8},
                "sessionAmbr": {"uplink": "200 Mbps", "downlink": "1 Gbps"}
            }
        }
    }

SUBSCRIBERS = [
    {"imsi": "208930000000003", "msisdn": "1234567891", "opc": "981d464c7c52eb6e5036234984ad0bcf", "key": "8baf473f2f8fd09487cccbd7097c6862"},
    {"imsi": "208930000000004", "msisdn": "1234567892", "opc": "981d464c7c52eb6e5036234984ad0bcf", "key": "8baf473f2f8fd09487cccbd7097c6862"}
]

def provision():
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    for sub in SUBSCRIBERS:
        imsi = sub['imsi']
        print(f"Provisioning {imsi}...")
        
        # 1. Auth Data
        db['subscriptionData.authenticationData.authenticationSubscription'].replace_one(
            {"ueId": f"imsi-{imsi}"}, 
            get_auth_subs_data(imsi, sub['opc'], sub['key']), 
            upsert=True
        )
        
        # 2. AM Data
        db['subscriptionData.provisionedData.amData'].replace_one(
            {"ueId": f"imsi-{imsi}", "servingPlmnId": "20893"},
            get_am_data(imsi, sub['msisdn']),
            upsert=True
        )
        
        # 3. SM Data (One per S-NSSAI usually, but simple structure here)
        # Note: SM Data key structure is complex in some versions. 
        # But commonly: ueId + servingPlmnId + singleNssai(sst+sd)
        # We will insert.
        sm_doc = get_sm_data(imsi)
        db['subscriptionData.provisionedData.smData'].replace_one(
             {"ueId": f"imsi-{imsi}", "servingPlmnId": "20893", "singleNssai.sst": 1, "singleNssai.sd": "010203"},
             sm_doc,
             upsert=True
        )
        
        print(f"[OK] {imsi} inserted into MongoDB.")

if __name__ == "__main__":
    provision()
