# ADR 0003 Make Approval and Simulated Posting Atomic

**Accepted · 2026-11-26**

A single full purchase order can be posted once, with a decision by an authorized approver distinct from the uploader. Concurrent requests and retries must preserve one ledger outcome and a complete audit record.

Store the simulated ERP in PostgreSQL. In one transaction verify the actor, report and order versions, current eligibility, and uniqueness. Commit the approval, ledger row, run state, and audit together. Use scoped uniqueness for invoice identity and full-order consumption. Scope decision idempotency to the actor and operation, returning the prior outcome for the same payload and rejecting conflicting reuse.

Separate approval and delivery would help integrate an external ERP but needs durable delivery and reconciliation. Use atomic posting for the simulated adapter. Revisit with a real ERP connector and demonstrate rollback, concurrent approval and posting, and stable idempotent replay against PostgreSQL.
