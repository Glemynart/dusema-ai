# ADR 0002 Separate Extraction from Deterministic Validation

**Accepted · 2026-11-26**

Invoice PDFs are variable in structure. Purchase orders are structured, and precision and traceability are required for decisions involving money.

Compare an extractor using templates and regular expressions with a model extractor using structured output. Both produce candidate fields and source evidence. Validate the candidates and enforce supplier and order matching, `ROUND_HALF_UP` decimal calculations, discrepancy handling, and eligibility in application code. A corrected value needs evidence from the invoice and a recorded revision. Unresolved discrepancies block posting.

A rules-only extractor is cheap and reproducible on known layouts. A model may improve recovery on new layouts and introduces cost, nondeterminism, and abstentions. Reference values isolate extraction quality from validation behavior. A versioned benchmark with a held-out split will determine what the model adds. Routine tests use offline fixtures.
