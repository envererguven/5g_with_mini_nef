# Free5GC Project (Docker/WSL2)

This project deploys a 5G Core Network using free5GC and Docker Compose.

## Project Status: Phase 1 (Control Plane Only)

Due to complexities with compiling the `gtp5g` kernel module on specific WSL2 kernels, the deployment is split into two phases.

### Phase 1: Control Plane (Active)
- **Goal**: Deploy AMF, SMF, NRF, UDM, UDR, PCF, AUSF, NSSF, CHF, and WebUI.
- **Status**: **Operational**.
- **Usage**:
    1.  Run `docker-compose up -d`.
    2.  Access WebUI at [http://localhost:5000](http://localhost:5000) (admin/free5gc).
    3.  Verify NFs are registered in the WebUI.

### Phase 2: User Plane (Deferred)
- **Goal**: Enable UPF for user traffic forwarding.
- **Requirement**: Install `gtp5g` kernel module in WSL2.
- **Current State**: The `upf` container is included but will fail/restart until `gtp5g` is installed.
- **Instructions**: See `GUIDE.md` for future steps on installing `gtp5g`.

## Documentation
- **[GUIDE.md](GUIDE.md)**: Detailed step-by-step instructions for running the network and (eventually) installing the kernel module.
- **[docker-compose.yaml](docker-compose.yaml)**: Service definitions.
- **[config/](config/)**: Configuration files for all Network Functions.
