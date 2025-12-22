# MongoDB Client README - Connect to Your Existing MongoDB Container

This guide shows you how to quickly and reliably connect to your **existing MongoDB container** (running on Docker Desktop) using **mongosh** — the official, modern, interactive MongoDB shell.

No need to install anything locally or run a permanent client container. We use a temporary, lightweight Docker container that starts, connects, and cleans itself up automatically.

Your MongoDB container is assumed to be running (check with `docker ps`). Common container names in free5GC setups are `mongodb`, `free5gc-mongodb`, etc.

## Connection Methods

### 1. Recommended: Share Network with Your MongoDB Container (Most Reliable)

```bash
docker run -it --rm --network container:mongodb mongo:latest mongosh


ALTERNATIVE: docker run -it --rm --network host mongo:latest mongosh "mongodb://localhost:27017"
AUTH 

# Container network method
docker run -it --rm --network container:mongodb mongo:latest mongosh "mongodb://username:password@localhost:27017"

# Host network method
docker run -it --rm --network host mongo:latest mongosh "mongodb://username:password@localhost:27017"


db.runCommand({ connectionStatus: 1 })
show dbs
use free5gc
show collections 
db.subscribers.find().limit(10).pretty()
db.subscribers.countDocuments({})
db.subscribers.find({ "ueId": "imsi-208930000000003" }).pretty()
db.subscribers.find({ "ueId": /20893/ }).pretty()
db.subscribers.findOne().pretty()


// 1. Connect using one of the commands above
// 2. Run these in mongosh:

use free5gc                    // Switch to your database
show collections               // See all tables/collections

// Example: View data in common free5gc collections
db.subscribers.find().pretty()
db.smPolicies.find().pretty()
db.sessionManagementData.find().pretty()
db.amPolicies.find().pretty()