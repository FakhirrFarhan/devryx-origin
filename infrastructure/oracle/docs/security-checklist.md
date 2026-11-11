# Security launch gate

- [ ] No secrets in Git, frontend bundles, logs or screenshots
- [ ] TLS enabled for all public hostnames
- [ ] Cloudflare Tunnel only; no public app/database/Redis ports
- [ ] Customer email verified before account activation
- [ ] OTP hashed, single-use, short expiry, attempt/resend throttles
- [ ] Session cookies Secure, HttpOnly, SameSite; session revocation works
- [ ] Every API resource checks tenant ownership server-side
- [ ] Admin registration disabled; owner role manually provisioned
- [ ] SENTINEL separate app, MFA/passkey, least privilege and audit log
- [ ] Upload type/size validation and private object storage
- [ ] Rate limits and abuse controls on login, OTP, generation and upload
- [ ] Dependency and container image scans completed
- [ ] Database and object-storage backups configured
- [ ] Restore drill completed and documented
- [ ] Monitoring and alerts tested
- [ ] Security review completed before real customer data
