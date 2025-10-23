# 📋 Public Backlog — Policy-as-Code Foundation (Open Source)

## Status Legend
- ✅ = done
- 🧩 = in progress
- 🚧 = planned
- ⚠️ = requires discussion

---

## 🎯 **Current Reality: Python Foundation**

### **What Works Now** ✅
- **Python Decision Functions**: Working examples (`examples/simple_demo.py`, `level1_basic_approval.py`, `level1_loan_approval.py`)
- **Progressive Learning**: Clear path from simple to complex decisions
- **Extensible Architecture**: FastAPI, PostgreSQL, Redis framework ready
- **OPA Infrastructure**: OPA binary and Rego policies exist but not integrated
- **Documentation**: Honest foundation status with roadmap to Agentic State

### **The Gap** ⚠️
- **Two Separate Systems**: Python examples and OPA/Rego policies exist independently
- **No Integration**: Users see Python examples but OPA/Rego system is hidden
- **Missing Bridge**: No way to progress from Python to OPA/Rego
- **CI/CD Missing**: No GitHub Actions workflows despite backlog claims

---

## P0 — Immediate (Foundation Integration)

### 1. Python-OPA Integration Bridge — 🚧
- Create Python wrapper for OPA evaluation
- Add `python3 examples/opa_demo.py` showing Rego policies
- Integrate Python examples with existing Rego policies
- Show users both Python and OPA approaches

### 2. Unified User Journey — 🚧
- Level 1: Python examples (current)
- Level 2: Python + OPA integration
- Level 3: Pure OPA/Rego policies
- Level 4: Production OPA bundles

### 3. Documentation Alignment — 🚧
- Update all docs to reflect Python foundation reality
- Add OPA integration examples
- Create migration path from Python to OPA
- Honest status indicators throughout

### 4. Basic CI/CD Setup — 🚧
- Add GitHub Actions workflow for Python examples
- Add OPA test workflow
- Add basic security scanning
- Add dependency updates (Dependabot exists)

---

## P1 — Short term (2–3 weeks)

### 5. OPA Bundle Creation — 🚧
- Create policy bundles from existing Rego files
- Add bundle validation and signing
- Integrate bundles with Python examples
- Add bundle testing in CI

### 6. Policy Schema Validation — 🚧
- Validate YAML policies against schema
- Add policy-validate job in CI
- Ensure registry → Rego entrypoint mapping
- Add JSONPath error output

### 7. Rego Test Coverage — 🚧
- Add `opa test --coverage` step
- Enforce ≥80% coverage
- Generate coverage summary in CI
- Add missing test cases

### 8. Security & Compliance — 🚧
- Add trivy for container scanning
- Add gitleaks for secret detection
- Verify OSI-approved dependencies
- Add REUSE compliance

---

## P2 — Medium (4–6 weeks)

### 9. Advanced OPA Features — 🚧
- Trusted bundle enforcement
- Policy drift detection
- Decision event schema
- Replay verification CLI

### 10. Production Readiness — 🚧
- Multi-environment promotion gates
- Performance benchmarks
- Public dashboard & alerts
- Build provenance and SBOM

---

## Meta / Governance

### 11. Community Guidelines — 🚧
- Update CODE_OF_CONDUCT.md
- Add SECURITY.md with contact info
- Update CONTRIBUTING.md for Python + OPA
- Add vulnerability reporting process

### 12. Versioning Policy — 🚧
- Define Python → OPA migration strategy
- Policy version mapping
- Backward compatibility tests
- Transparency reporting

---

## Done Definition (Foundation Integration)
- Python examples work and are documented ✅
- OPA/Rego policies work and are tested ✅
- Integration bridge between Python and OPA 🚧
- Unified user journey from Python to OPA 🚧
- Basic CI/CD with Python and OPA tests 🚧
- Honest documentation reflecting reality 🚧
- Community guidelines and security process 🚧
