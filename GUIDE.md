# Free5GC Deployment Guide for Windows 11 (WSL2)

This guide helps you deploy the free5GC Core Network.
**Note:** The deployment is split into two phases due to WSL2 kernel dependencies.

## Phase 1: Control Plane Deployment (Current)

This phase deploys the management and control NFs (AMF, SMF, NRF, WebUI, etc.).
**Expected Outcome:** All containers *except* UPF will run. You can access the WebUI.

### Step 1: Start the Network

1.  Open **PowerShell** as Administrator.
2.  Navigate to the project folder:
    ```powershell
    cd C:\Users\PCUser\.gemini\antigravity\scratch\free5gc_project
    ```
3.  Run Docker Compose:
    ```powershell
    docker-compose up -d
    ```

### Step 2: Verify Control Plane

1.  Check container status:
    ```powershell
    docker-compose ps
    ```
    *   **Success**: `nrf`, `amf`, `smf`, `udm`, `udr`, `pcf`, `ausf`, `nssf`, `chf`, `webui`, `db` should be **Up**.
    *   **Expected Failure**: `upf` may be `Restarting` or `Exited` because the `gtp5g` module is missing. **Ignore this for now.**

2.  Access the WebUI:
    *   URL: [http://localhost:5000](http://localhost:5000)
    *   User: `admin`
    *   Pass: `free5gc`

### Step 3: Test UE Registration (Control Plane)

1.  **Start the UERANSIM container**:
    ```powershell
    docker-compose up -d ueransim
    ```

2.  **Monitor the gNodeB logs** to ensure it connects to the AMF:
    ```powershell
    docker-compose logs -f ueransim
    ```
    *   Look for: `[GNB] SCTP connection established with AMF` and `NG Setup accepted`.
    *   Press `Ctrl+C` to exit logs.

3.  **Register a UE**:
    Open a new terminal and run:
    ```powershell
    docker exec -it ueransim ./nr-ue -c ./config/uecfg.yaml
    ```

4.  **Expected Output**:
    *   ✅ **Registration**: You should see `[NAS] Registration accept`.
    *   ❌ **PDU Session**: You will likely see `[NAS] PDU session establishment reject` or timeouts because the UPF is not running (Phase 2 deferred).
    *   **WebUI**: Check the "Subscribers" tab in the WebUI to see the connected UE status.

### Step 4: Access MongoDB

You can connect to the database using a GUI tool (like MongoDB Compass) or CLI.

*   **Connection String**: `mongodb://localhost:27017`
*   **Database Name**: `free5gc`
*   **Username**: *(None / Leave empty)*
*   **Password**: *(None / Leave empty)*

> **Note**: If you cannot connect, ensure you applied the latest changes by running `docker-compose up -d`.

### Step 5: Traffic Capture (tcpdump)

To capture traffic from a specific Network Function (e.g., AMF, SMF) without installing tools inside it, use a **sidecar container**.

**Command:**
```powershell
# Syntax: docker run --rm --net container:<container_name> -v ${PWD}/capture:/data nicolaka/netshoot tcpdump -i any -w /data/<filename>.pcap

# Example: Capture AMF traffic
docker run --rm --net container:amf -v ${PWD}/capture:/data nicolaka/netshoot tcpdump -i any -w /data/amf.pcap
```

1.  Run the command in a separate terminal.
2.  Perform your tests (e.g., register UE).
3.  Press `Ctrl+C` to stop the capture.
4.  The `.pcap` file will be saved in a `capture` folder in your project directory. You can open it with Wireshark.

---

## Phase 2: User Plane Enablement (Deferred)

**Goal:** Enable the UPF for actual data traffic.
**Requirement:** Install `gtp5g` kernel module in WSL2.

> **Status:** This step is currently deferred due to WSL2 kernel compilation complexity.

### Future Steps to Enable UPF:
1.  Resolve WSL2 kernel header issues (requires matching source code).
2.  Compile and install `gtp5g` in the WSL2 environment.
3.  Restart the UPF container: `docker-compose restart upf`.

---

## Directory Structure
-   `docker-compose.yaml`: Service definitions.
-   `config/`: Configuration files for all NFs.
