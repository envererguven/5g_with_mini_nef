# Free5GC Deployment Guide (eUPF + Advanced Networking)

This guide deploys a 5G Core Network using **eUPF** (eBPF-based UPF), eliminating the need for custom kernel modules.

## Architecture
*   **Core**: free5GC (AMF, SMF, etc.)
*   **User Plane**: eUPF (ghcr.io/edgecomllc/eupf)
*   **RAN**: UERANSIM (gNB + UE)
*   **Monitoring**: Netshoot container attached to eUPF

## Prerequisites
*   Windows 11 + Docker Desktop (WSL2 backend)
*   **No** custom kernel compilation required!

## Step 1: Start the Network

1.  **Clean up old containers** (if any):
    ```powershell
    docker-compose down -v
    ```

2.  **Start the new stack**:
    ```powershell
    docker-compose up -d
    ```

3.  **Verify Status**:
    ```powershell
    docker-compose ps
    ```
    *   Ensure `eupf`, `amf`, `smf`, `ueransim-gnb` are **Up**.

## Step 2: Verify Control Plane

1.  Access WebUI: [http://localhost:5000](http://localhost:5000) (admin/free5gc).
2.  Check "Network Functions": You should see AMF, SMF, UPF (eUPF), etc. registered.

## Step 3: Verify User Plane (Ping Test)

1.  **Register the UE**:
    ```powershell
    docker exec -it ueransim-ue ./nr-ue -c ./config/uecfg.yaml
    ```
    *   Expected: `[NAS] Registration accept` and `[NAS] PDU session establishment accept`.

2.  **Test Connectivity**:
    In the UE terminal (or a new one):
    ```powershell
    docker exec -it ueransim-ue ping -I uesimtun0 8.8.8.8
    ```
    *   **Success**: You should see ping replies!

## Step 4: Network Monitoring

The `network-monitor` container is attached to the `eupf` service, giving you visibility into N3 (GTP), N4 (PFCP), and N6 (Internet) traffic.

**Capture Traffic:**
```powershell
# Capture all traffic on N3 interface (GTP-U)
docker exec -it network-monitor tcpdump -i n3 -nn

# Capture PFCP traffic on N4
docker exec -it network-monitor tcpdump -i n4 port 8805

# Save capture to file (inside container)
docker exec -it network-monitor tcpdump -i any -w /tmp/capture.pcap
```

## Step 5: Northbound API (Mini-NEF)

The **Mini-NEF** exposes a simple REST API to resolve IP addresses to MSISDNs.
*Note: Due to a missing BSF Docker image, this service currently uses a fallback mechanism (Mock/Direct DB) to simulate the resolution.*

> [!TIP]
> **New:** API Documentation (Swagger UI) is available at [http://localhost:9090/apidocs](http://localhost:9090/apidocs).

1.  **Start Services**:
    ```powershell
    docker-compose up -d mini-nef
    ```

2.  **Verify Service is Running**:
    Open browser or curl the root to see the Welcome message:
    ```powershell
    curl.exe "http://localhost:9090/"
    ```

3.  **Provision Sample Subscriber**:
    Run the provisioning script to insert the test MSISDN (1234567890) into the Core:
    ```powershell
    python provision_subscriber.py
    ```

4.  **Test the API (with JSON Prettify)**:
    In PowerShell, pipe the output to format it nicely:
    ```powershell
    curl.exe "http://localhost:9090/identity?ip=10.60.0.1" | ConvertFrom-Json | ConvertTo-Json
    ```
    
    Expected Response:
    ```json
    {
        "ip": "10.60.0.1",
        "msisdn": "1234567890",
        "source": "Mock/Fallback",
        "supi": "imsi-208930000000003"
    }
    ```

## Step 6: Testing Additional APIs

The Mini-NEF supports these additional endpoints. Full documentation is available in the **Swagger UI** (`/apidocs`).

### 1. SIM Swap Check
**Goal**: Check if a SIM card has been swapped recently.

*   **Swagger**: `GET /sim-swap`
*   **Parameters**: `msisdn` (query)

```powershell
curl.exe "http://localhost:9090/sim-swap?msisdn=1234567890" | ConvertFrom-Json | ConvertTo-Json
```
**Expected Output**:
```json
{
    "last_swap_timestamp": "2024-01-01T12:00:00Z",
    "msisdn": "1234567890",
    "swapped": false
}
```

### 2. Location API
**Goal**: Retrieve the geolocation of a subscriber.

*   **Swagger**: `GET /location`
*   **Parameters**: `msisdn` (query)

```powershell
curl.exe "http://localhost:9090/location?msisdn=1234567890" | ConvertFrom-Json | ConvertTo-Json
```
**Expected Output**:
```json
{
    "accuracy": 100,
    "latitude": 40.7128,
    "longitude": -74.006,
    "msisdn": "1234567890",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### 3. Quality on Demand (QoD)
**Goal**: Request a QoS session for an IP address.

*   **Swagger**: `POST /qos/sessions`
*   **Parameters**: JSON Body (`ueIpv4`, `qosProfile`, `duration`)

**Command**:
```powershell
curl.exe -X POST -H "Content-Type: application/json" -d '{\"ueIpv4\": \"10.60.0.1\", \"qosProfile\": \"low-latency\"}' "http://localhost:9090/qos/sessions" | ConvertFrom-Json | ConvertTo-Json
```
**Expected Output** (Status 201 Created):
```json
{
    "duration": 3600,
    "qosProfile": "low-latency",
    "sessionId": "qos-ses-12345",
    "status": "active"
}
```

## Step 7: SMS Services (IMS-Lite)

Since the core network lacks a native SMSF, we use an **IMS-Lite** approach (SIP MESSAGE) via the `mini-smsc` component.

### Prerequisites
*   Ensure **two** UEs are running (`ueransim-ue` and `ueransim-ue2`).
*   Ensure both are provisioned via `python provision_subscriber.py`.
*   Ensure `sip_client.py` is available (you may need to copy it into the container or likely just type the commands if python is present).

### 1. P2P SMS (UE1 ↔ UE2)

**Scenario**: UE1 (`1234567891`) sends a message to UE2 (`1234567892`).

1.  **Prepare UE1 (User A)**:
    Open a terminal:
    ```bash
    # Copy script to container (if mostly text, or use docker cp)
    docker cp sip_client.py ueransim-ue:/app/sip_client.py
    
    # Enter UE1
    docker exec -it ueransim-ue bash
    # (Inside UE) Install python if missing
    apt-get update && apt-get install -y python3
    
    # Register UE1 (Bind to its tunnel IP, usually 10.60.0.1)
    python3 sip_client.py register --sip-user 1234567891 --local-ip 10.60.0.1
    ```

2.  **Prepare UE2 (User B)**:
    Open a second terminal:
    ```bash
    docker cp sip_client.py ueransim-ue2:/app/sip_client.py
    
    docker exec -it ueransim-ue2 bash
    # (Inside UE2)
    apt-get update && apt-get install -y python3
    
    # Register UE2 (Bind to its tunnel IP, usually 10.60.0.2)
    python3 sip_client.py register --sip-user 1234567892 --local-ip 10.60.0.2
    
    # Start Listening
    python3 sip_client.py listen --local-ip 10.60.0.2
    ```

3.  **Send Message (UE1 -> UE2)**:
    Back in **UE1** terminal:
    ```bash
    python3 sip_client.py send --sip-user 1234567891 --to 1234567892 --msg "Hello from User A!"
    ```
    *   **Result**: You should see the message appear in the **UE2** terminal listener.

### 2. A2P SMS (Application ↔ UE1)

**Scenario**: Send a marketing message from the API to UE1.

1.  **Ensure UE1 is Registered** (see above).
2.  **Send via API** (from Host):
    ```powershell
    curl -X POST -H "Content-Type: application/json" -d '{\"to\": \"1234567891\", \"body\": \"Your OTP is 9999\", \"from\": \"Bank\"}' "http://localhost:9090/sms/send"
    ```
3.  **Verify**: Check UE1 listener or logs.
