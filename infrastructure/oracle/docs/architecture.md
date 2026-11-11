# DEVRYX target architecture

```text
Customers
   |
Cloudflare DNS / HTTPS / WAF / rate controls
   |
Cloudflare Tunnel (outbound from Oracle VM)
   |
Oracle Ubuntu VM
   |-- Frontend (private Docker network)
   |-- Backend API (private Docker network)
   |-- Persistent job scheduler/worker service (to be implemented)
   |
Neon PostgreSQL (TLS; backend only)
   |
Private object storage (customer assets + off-device copies)

Windows laptop (optional authenticated AI worker)
   |-- Development and small experiments
   |-- Local model/dataset workspace
   |-- Polls cloud job queue only while awake
```

The laptop is not the source of truth for accounts or job records. The cloud database is.
Customer-critical media must be copied to cloud object storage if it must remain downloadable while the laptop is offline.
