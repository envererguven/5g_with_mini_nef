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
