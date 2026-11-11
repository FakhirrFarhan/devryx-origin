# DEVRYX AI — Oracle + Hybrid Infrastructure Starter

This package is a **deployment scaffold**, not a finished production platform. It is tailored for:
- Oracle Cloud Always Free target (Ubuntu ARM64 / Ampere A1 where available)
- Windows 11 development laptop with 8 GB RAM
- Existing domain managed through Cloudflare
- Neon-hosted PostgreSQL
- Hybrid storage: cloud for customer-critical files; laptop for development/model experiments

## What this package does
- Provides a Docker Compose scaffold for a Next.js frontend and FastAPI backend.
- Keeps app services bound to localhost on the VM.
- Provides a Cloudflare Tunnel configuration template.
- Provides Oracle Ubuntu bootstrap and firewall scripts.
- Provides encrypted Restic backup script templates.
- Provides environment-variable templates and deployment checklists.

## What it does NOT do
The scaffold does not implement customer registration, email OTP, sessions, tenant isolation, billing, support tickets, SENTINEL authorization, a real job queue, laptop worker, or AI inference/training. Do not expose it to customers as a secure production service until those features are implemented and tested.

## 1. Prepare Oracle Cloud
Create an eligible Always Free Ampere A1 instance if capacity is available:
- Ubuntu 24.04 ARM64
- Start with 2 OCPUs and 12 GB RAM if the console confirms Always Free eligibility
- 50 GB boot volume (check the free allowance and total volume usage)
- Add an SSH public key
- Do not upgrade to paid resources merely to bypass capacity limits

Connect from Windows PowerShell:
```powershell
ssh -i "$HOME\.ssh\devryx-production.key" ubuntu@YOUR_ORACLE_PUBLIC_IP
```

Copy this folder to the server:
```powershell
scp -i "$HOME\.ssh\devryx-production.key" -r .\DEVRYX-Oracle-Infrastructure-Starter ubuntu@YOUR_ORACLE_PUBLIC_IP:/home/ubuntu/
```

## 2. Bootstrap the VM
On the VM:
```bash
cd ~/DEVRYX-Oracle-Infrastructure-Starter
chmod +x scripts/*.sh
./scripts/oracle-bootstrap.sh
```
The firewall script allows SSH only for initial access and denies other inbound ports. Do not run it before confirming SSH works and you have your SSH key available.

## 3. Add your existing DEVRYX application
Copy your existing project into this folder as:
```
app/
  frontend/
  backend/
```
The frontend must have a working production Dockerfile at `app/frontend/Dockerfile`.
The backend must have a working production Dockerfile at `app/backend/Dockerfile`.
The compose file expects the frontend on port 3000 and backend on port 8000 inside their containers.

Important: your current DEVRYX prototype is not production-ready. Its API has in-memory jobs and no authentication/authorization/database ownership enforcement. This scaffold does not silently fix those issues.

## 4. Configure secrets
```bash
cp .env.example .env
nano .env
chmod 600 .env
```
Fill in real values. Never commit `.env`. Use a password manager for secrets. `DATABASE_URL` is for server-side backend use only.

## 5. Start services
After adding app code and Dockerfiles:
```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs --tail=100
```
The compose file binds services to `127.0.0.1`, so they are not directly public. It includes no public database or Redis port.

## 6. Cloudflare Tunnel
1. Add your domain to Cloudflare and update nameservers at your registrar.
2. Preserve existing MX, SPF, DKIM and DMARC records if your domain uses email.
3. In Cloudflare Zero Trust, create a named tunnel `devryx-production`.
4. Install `cloudflared` using the exact Linux ARM64 command Cloudflare displays.
5. Put the tunnel credentials JSON at `./secrets/cloudflared.json` (create `secrets/`; restrict permissions).
6. Edit `cloudflared/config.yml` and replace `YOUR_DOMAIN`.
7. Add the tunnel service to compose by uncommenting the marked block after verifying the credential file path.
8. Configure hostname routes:
   - `app.YOUR_DOMAIN` -> `http://frontend:3000`
   - `api.YOUR_DOMAIN` -> `http://backend:8000`
   - `sentinel.YOUR_DOMAIN` -> do not route until a separately secured owner app exists
   - `www.YOUR_DOMAIN` -> configure only when the public website exists

Cloudflare Tunnel is outbound-initiated. Keep application ports private. Use Cloudflare Access as an additional gate for the owner panel, but still implement application-level owner authorization.

## 7. Database
Create a Neon PostgreSQL project and place its SSL connection string in `DATABASE_URL`. This scaffold does not create migrations or database tables. Before production, implement migrations and ownership constraints for users, sessions, OTPs, projects, jobs, assets, credit transactions, subscriptions, support tickets, audit logs, admin roles and worker devices.

## 8. Backups
Install Restic:
```bash
sudo apt install -y restic
```
Create an encrypted repository on a separate external destination (for example an S3-compatible object storage bucket). Set `RESTIC_REPOSITORY`, `RESTIC_PASSWORD_FILE`, and any required S3 credentials in a root-readable environment file outside the Git repository. Review `scripts/backup-restic.sh`, then test it:
```bash
sudo /opt/devryx/backup.env
sudo /opt/devryx/backup-restic.sh
```
The example script intentionally exits if configuration is missing. Do not store the only backup on the same VM or same disk as the source data. Oracle's free object storage allowance is small; do not assume it can hold all generated videos.

Recommended:
- Database backup: hourly (use a managed database backup/PITR feature where available, plus logical dumps)
- Critical customer assets: upload to cloud object storage when created
- VM configuration and application data: nightly
- Model checkpoints: after each valuable checkpoint
- Restore test: monthly at minimum, preferably weekly

## 9. Laptop sleep / worker behavior
The online app and database must not depend on the laptop being awake. If the laptop sleeps, jobs should remain queued in the database. A worker must authenticate, poll for eligible jobs, renew a lease/heartbeat, and safely resume/retry. This worker is NOT implemented in this package.

Files stored only on the laptop are unavailable while it sleeps. Sync customer-critical files to cloud object storage.

## 10. Before public launch
- Implement verified email OTP with hashed, short-lived, single-use codes and send/attempt limits.
- Implement secure sessions, CSRF protections where applicable, password/passkey policy, and logout/revocation.
- Enforce tenant ownership on every backend read/write/download.
- Implement separate owner-only SENTINEL application and audited admin actions.
- Add persistent jobs, retries, idempotency, worker leases and failure handling.
- Add private object storage and signed downloads.
- Add rate limits, request size limits, upload validation, malware scanning where appropriate.
- Pin dependencies; scan dependencies and container images.
- Configure monitoring, alerting, log redaction, database backups and tested restores.
- Perform security testing (OWASP ASVS-aligned) and independent review before accepting customer data.

No system is 100% secure. This starter is a foundation for deployment work, not a security certification.
