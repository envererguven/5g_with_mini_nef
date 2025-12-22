# Free5GC with eUPF (No Kernel Module)

This project deploys a 5G Core Network using **eUPF** (eBPF-based UPF), bypassing the need for custom kernel modules in WSL2.

## Architecture
-   **Core NFs**: AMF, SMF, NRF, UDR, UDM, AUSF, NSSF, PCF, BSF, CHF.
-   **User Plane**: **eUPF** (ghcr.io/edgecomllc/eupf).
-   **RAN**: UERANSIM (gNB + UE).
-   **Monitoring**: `network-monitor` (Netshoot) attached to eUPF.
-   **Management**: WebUI (Port 5000).

## Network Topology
-   **mgmt** (10.100.200.0/24): SBI & Management.
-   **n2** (172.18.1.0/24): AMF <-> gNB.
-   **n3** (172.18.2.0/24): gNB <-> UPF (GTP-U).
-   **n4** (172.18.3.0/24): SMF <-> UPF (PFCP).
-   **n6** (172.18.4.0/24): UPF <-> Internet.

## Quick Start

1.  **Start the Network**:
    ```powershell
    docker-compose up -d
    ```

2.  **Verify Services**:
    ```powershell
    docker-compose ps
    ```

3.  **Access WebUI**:
    -   URL: [http://localhost:5000](http://localhost:5000)
    -   User: `admin`
    -   Pass: `free5gc`

4.  **Test Connectivity (Ping)**:
    ```powershell
    docker exec -it ueransim-ue ping -I uesimtun0 8.8.8.8
    ```

5.  **Monitor Traffic**:
    ```powershell
    # Capture N3 (GTP) traffic
    docker exec -it network-monitor tcpdump -i n3 -nn
    ```

## Troubleshooting
-   **eUPF Errors**: Ensure you have `SYS_ADMIN` cap enabled (already in compose).
-   **No Ping**: Check if `ueransim-ue` registered successfully (`docker logs ueransim-ue`).
