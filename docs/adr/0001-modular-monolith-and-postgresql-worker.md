# ADR 0001 Adopt a Modular Monolith and PostgreSQL Worker

**Accepted · 2026-11-26**

Invoice extraction can outlast a request and needs durable recovery. The team is one developer, and the demo workload can share a database.

Use one Python application codebase with separate web and worker processes. FastAPI serves the API and Jinja2 review pages. PostgreSQL stores business state and extraction jobs. The worker claims jobs with leases and ownership checks. Keep model, storage, and ERP connections behind typed adapters. Run dependencies locally through Docker Compose as the persistence increment lands.

An in-process background task would be simpler to start, with recovery tied to the web process. A dedicated broker or separate service could handle higher parallelism, but adds deployment and consistency work. Review the decision when job throughput, database contention, or independent deployment becomes a measured constraint. Verify lease expiry, recovery, and stale-attempt rejection before relying on the worker.
