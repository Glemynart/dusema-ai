# Initial Authentication and Security Policy

These are implementation criteria for the demo workflow. The first Foundation increment exposes a public liveness response with no user or system metadata. Identity and authorization will be implemented before protected business features are exposed.

## Identity and authorization

- Seed separate local accounts for the analyst, approver, and auditor using explicit setup with test-only credentials. Hash stored passwords with Argon2id using a maintained library. Use generic sign-in failures, rate limit login attempts, and keep any dev reset command local. [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- Derive identity and organization from an active server-side session and membership. Verify the role, organization, resource access, and workflow state on every protected request. Apply organization scope to repository lookups and file access. Deny direct posting requests that bypass the approved workflow.
- Analysts submit, review, and correct their own uploads. Approvers can read relevant organization records and decide, but cannot approve an invoice they uploaded. Auditors have organization-scoped read-only access. Demo fixture administration remains a local operator activity. A duplicate upload must never reveal a run identifier or document to a user without access to that record.

## Sessions and state-changing requests

- Use an opaque, cryptographically random session identifier and keep the session state server-side. Rotate the identifier on sign-in and any privilege change. Revoke it on logout and on membership loss. Initial timeout proposal is 30 minutes idle and 8 hours absolute, with both enforced server-side. [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- Set a host-only session cookie with `HttpOnly`, `SameSite=Lax`, and `Path=/`. Require `Secure` over HTTPS and enforce HTTPS for hosted environments. Plain HTTP is an explicit loopback development mode. Send no session identifiers in URLs or logs.
- Keep safe HTTP methods read-only. Protect login, logout, upload, corrections, approvals, and other mutations with a server-validated CSRF token bound to the session and trusted-origin checks. Create a short-lived pre-authentication session for the login form and rotate it after login. Reject missing or mismatched tokens and cross-origin submissions before changing state. Serve the demo UI and API on one origin. [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- Check the current report revision, uploader separation, duplicate constraints, and order eligibility in the posting transaction. Treat idempotency keys and CSRF tokens as separate controls. Record the authorized actor and report revision in the audit trail.

## Verification before exposing business endpoints

Automate tests for absent, expired, rotated and revoked sessions, each permitted role, access to another user's or organization's records, read-only auditor behavior, uploader approval denial, rejected CSRF or origin checks, and valid same-origin requests. Verify that no rejected mutation writes an invoice, posts to the simulated ERP, or advances the workflow. Confirm cookies, redaction, and private file access in the environment that serves the demo.

## GitHub repository security controls

The public GitHub repository has these free repository-level controls enabled:

- Dependency graph, Dependabot alerts, and Dependabot security updates for supported dependencies and GitHub Actions.
- Secret scanning and repository-level push protection.
- CodeQL default setup for Python and GitHub Actions on standard GitHub-hosted runners.
- The CI workflow keeps its token permission limited to `contents: read`; CodeQL uses its GitHub-managed, scoped analysis workflow.
