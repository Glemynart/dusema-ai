# DUSEMA AI Release Roadmap

## V0.1 Intelligent Document Processing

Deliver the invoice-to-purchase-order workflow using synthetic Spanish PDFs and orders in COP. Include structured extraction with page evidence, deterministic validation, duplicate prevention, an approval queue, idempotent simulated ERP posting, and audit history.

| Increment | Completion evidence |
| --- | --- |
| Discovery | Approved scope, acceptance examples, security policy, ADRs, and Definition of Done |
| Foundation application | Reproducible local Python environment, FastAPI liveness route, tests, quality checks, and CI configuration |
| Foundation persistence | Verified locally. PostgreSQL starts with Compose, application sessions commit and roll back, liveness and database readiness report independently, and Alembic applies the organization migration from a clean database |
| Foundation identity | Seeded local accounts, server-managed sessions, CSRF protection, and organization-scoped role checks are verified before protecting business workflows |
| AI Core | Baseline, fixture, and model extractors share a schema, persist provenance, and expose failure and usage outcomes. Paid live calls require approval |
| Invoice workflow and review UI | A local demo demonstrates valid posting, commercial discrepancies, duplicates, human decisions, and audit |
| Evaluation and portfolio | Reproducible results compare template and regex extraction, LLM extraction, and reference values using the 36/24 dataset split. A portfolio walkthrough explains the design and measured limitations |

## V0.2 Enterprise Finance Agent

Let a Finance Agent select approved tools to consult suppliers, orders, existing invoices, and business rules, investigate discrepancies, request missing information, and prepare recommendations and proposed actions. Evaluate Function Calling, Tool Calling, and persisted agent state. Consider LangGraph if branching and resumption requirements justify a graph runtime.

Compare the agent against the deterministic workflow on the same cases. Report task completion, correct tool selection, unnecessary calls, latency, cost, failure modes, and authorization outcomes. Gate critical operations on explicit permission, deterministic validation, and human approval.

## V0.3 Enterprise Knowledge Agent

Add document ingestion, chunking, embeddings, permission-aware retrieval, hybrid search, and references to original evidence. Compare retrieval quality across semantic and hybrid configurations and use annotated results to assess citation accuracy. Evaluate pgvector, indexing, and reranking against the retrieval workload.

## V0.4 Enterprise Agent Orchestration

Add specialized agents, enterprise integrations, and MCP where interoperability provides a concrete advantage. Introduce coordination for workflows with real inter-agent dependencies and evaluate it against one agent or a deterministic workflow. Keep execution limits, budgets, permissions, and recovery explicit. Reassess LangChain, Redis, asynchronous queues, and service separation as demonstrated usage warrants.

## V1.0 Enterprise AI Workforce

Integrate the proven modules into an enterprise platform with security, evaluation, observability, cloud deployment, and reproducible documentation. Assess Azure as the first cloud option under separate authorization. Consider a dedicated Next.js review interface or service separation if interaction complexity, ownership, scale, or fault isolation justify them.

V0.2 and later describe direction. Their implementation depends on the preceding release and a concrete use case.
