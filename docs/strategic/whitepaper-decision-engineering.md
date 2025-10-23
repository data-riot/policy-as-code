# White Paper: Decision Engineering Foundation for Accountable Automation

**Author:** Eevamaija Virtanen
**Date:** October 2025
**Status:** Foundation Implementation

---

## 1. Executive Summary

Finland has built world-class digital infrastructure that enable secure data exchange and human-centric digital services. However, as automation and artificial intelligence become part of governance, the legal basis of automated decisions is becoming opaque.

This paper proposes a new national capability: **Decision Engineering** — an operational architecture that connects legislation, automated decision logic, and audit evidence.

**Current Implementation**: We have built a **Policy as Code Foundation** that provides the essential building blocks for Decision Engineering. This foundation includes working decision functions, extensible architecture, and a clear roadmap toward full Decision Engineering capabilities.

**Future Vision**: Decision Engineering will define every automated decision as a **Decision Function**: a formally described, signed, and auditable unit of logic linked directly to its legal section (Finlex ELI URI). When a system or AI agent executes such a function, the action will be automatically lawful, traceable, and explainable.

The approach enables Finland to automate with integrity — strengthening legal certainty, transparency, and efficiency without new legislation.

**EU AI Commons Vision**: This Decision Engineering framework serves as the foundation for an EU AI Commons, enabling cross-border collaboration and shared AI infrastructure across European Union countries. See [EU AI Commons Strategy](nordic-ai-commons.md) for the complete cross-border vision.

**Sources**: This whitepaper is based on Finnish government digital infrastructure including Finlex, Finnish Government APIs, DVV Population Information System, Kanta Services, and AuroraAI initiatives.

---

## 2. Current Foundation Status

### **What We Have Built**

**Policy as Code Foundation** provides:
- **Working Decision Functions** - Simple business logic with validation
- **Progressive Learning Examples** - Loan approval, basic approval, multi-criteria decisions
- **Extensible Architecture** - FastAPI, PostgreSQL, Redis, monitoring stack
- **Clear Documentation** - Comprehensive guides and architecture docs

### **What We're Building Toward**

**Decision Engineering** will provide:
- **Legal Binding** - Direct links to Finlex/EUR-Lex sections
- **Digital Signatures** - Change control and separation of duties
- **Immutable Trace Ledger** - Hash-chained audit trail
- **Agentic AI Integration** - LLM-powered reasoning

---

## 3. Rationale

---

## 3. Core Concept: Decision Function

Each Decision Function (DF) is a modular rule representing a specific section of law:

```
DecisionFunction(
    id: string,
    version: semver,
    law_reference: URI,
    owner: ministry_id,
    inputs_schema: JSON Schema,
    outputs_schema: JSON Schema,
    logic_hash: SHA256,
    signatures: [owner_sign, reviewer_sign]
)
```

- **Law reference**: direct ELI URI pointing to Finlex section
- **Logic**: deterministic rule (no randomness or external I/O)
- **Signatures**: digital signatures by the responsible ministry and a reviewer
- **Execution**: always via a secure API; results logged in an immutable ledger
- **Explainability**: each decision produces a human-readable rationale with the legal basis

This makes law executable without losing human accountability.

---

## 4. System Architecture

The national architecture has four layers:

| Layer | Function | Owner |
|-------|----------|-------|
| **Normative Layer** | Law text and legislative metadata (Finlex ELI) | Legal Register Centre |
| **Model Layer** | Decision Functions with formal schemas and logic | Legal Engineering Office |
| **Execution Layer** | Systems and agents calling DFs via Finnish Government APIs | Agencies |
| **Integrity Layer** | Immutable Trace Ledger and Audit Service verifying lawful execution | Audit & Integrity Agency |

**Core components:**
- **Decision Registry**: national repository of all signed DFs
- **Trace Ledger**: append-only, hash-chained record of every DF execution
- **Explain API**: public endpoint to view the reasoning behind a decision
- **Audit Service**: independent verifier that replays traces and reports drift

---

## 5. Alignment with Existing Infrastructure

| Existing asset | Use in Decision Engineering |
|----------------|----------------------------|
| **Finlex / ELI** | Legal identifiers for all laws and sections (used as DF references) |
| **Finnish Government APIs** | Secure data exchange layer for DF API traffic between agencies |
| **DVV Population Information System** | Canonical ontology for person and address data |
| **Kanta Services** | Model for immutable logging and access audit discipline |
| **AuroraAI** | Human-centric orchestration layer that will call DFs for lawful automation |

The model requires no new base systems — only a shared Decision Function registry, signatures, and an audit ledger.

---

## 6. Implementation Plan (2026–2028)

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **1. Standards & Pilot** | Q1–Q3 2026 | DF Spec v1.0 JSON Schema; Registry prototype; Pilot with Kela or Traficom (10 DFs) |
| **2. Scale Up** | Q4 2026–Q4 2027 | Two more ministries onboarded; public Explain API; first annual audit report |
| **3. Institutionalization** | 2028 | Legal Engineering Office and Decision Registry Authority formalized; integration with AuroraAI flows |

**Pilot metrics:**
- ≥ 90% of automated decisions within pilot domain executed via DF API
- 0 unsigned DF executions
- Citizen explanation delivered within 1 second of query
- Audit drift < 1%

---

## 7. Governance and Roles

| Institution | Responsibility |
|-------------|----------------|
| **Legal Engineering Office (LEO)** | Translates laws into formal Decision Functions |
| **Decision Registry Authority (DRA)** | Maintains registry, manages keys and versions |
| **Audit & Integrity Agency (AIA)** | Runs continuous audit and publishes integrity reports |
| **Agencies / Municipalities** | Integrate DF APIs into operational systems |
| **Citizens / Oversight bodies** | Access explanations and challenge incorrect decisions |

**Governance principles:**
- Law remains the ultimate authority
- Decision logic cannot diverge from its legal reference
- All automation is explainable and reversible

---

## 8. Cost and Benefits

**Estimated national cost:**
- 2026: €1.2 million (standards + pilot)
- 2027: €2.4 million (scale-up)
- 2028: €3.0 million (institutionalization)

**Benefits:**
- Elimination of opaque rule code
- Reusable decision logic across ministries
- Lower audit and appeals workload
- Increased citizen trust through explainability
- Global leadership in accountable automation

---

## 9. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| **Legal interpretation drift** | Dual sign-off by jurist and engineer; periodic re-validation |
| **Privacy exposure in explanations** | Declarative redaction list in each DF Spec |
| **Skills shortage** | National training programme for policy engineers |
| **Over-centralization** | Federated registries under shared schema and audit protocol |

---

## 10. Recommendation

The Ministry of Finance should establish a national Decision Engineering programme in 2026 with the following mandates:

1. **Adopt** the Decision Function Spec and Registry standard
2. **Launch** a pilot in one benefit or licensing domain
3. **Fund** a small permanent Legal Engineering Office
4. **Create** an inter-ministerial working group for the Audit & Integrity Agency concept

This initiative operationalizes Finland's digital-government principles: legality, transparency, and human-centricity — not by replacing law with code, but by ensuring that code itself is lawful.

---

*End of White Paper*
