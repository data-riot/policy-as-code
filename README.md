# Policy as Code - Production Governance Platform

A production-grade platform for managing decision logic as versioned, auditable, and governable software artifacts with comprehensive governance features.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

Policy as Code provides a comprehensive governance platform for managing decision logic with enterprise-grade features including immutable trace ledgers, digital signatures, legal compliance, and independent audit capabilities.

### 🚀 Key Features

- **🔒 Immutable Trace Ledger** - Append-only ledger with hash-chaining and signer identity
- **📜 Legal Compliance** - First-class legal linkage with validated IRIs (Finlex/EUR-Lex)
- **✍️ Digital Signatures** - Change control with owner/reviewer signatures and separation of duties
- **🔍 Independent Audit** - Separate audit service for integrity verification and drift detection
- **📊 Deterministic Execution** - Time semantics and point-in-time feature store for replay consistency
- **🎯 Formal DSL** - Rule-based DSL with priorities, conflict detection, and static analysis
- **📈 Testing SLOs** - 100% branch coverage, mutation testing, and contract validation
- **📋 Analytics Schema** - BigQuery/Snowflake DDL with canonical queries
- **⚡ Production Ready** - Circuit breakers, retry policies, and operational SLOs

## 🏃‍♂️ Quick Start (30 Minutes)

### Golden Path Demo

```bash
# Clone and setup
git clone <repository-url>
cd policy_as_code

# Install dependencies
make install

# Run the complete golden path demo
make golden_path_demo
```

This will demonstrate:
1. ✅ Bootstrap registry and services
2. ✅ Register decision functions (Python + DSL)
3. ✅ Define legal references
4. ✅ Create and sign releases
5. ✅ Execute decisions with traces
6. ✅ Run independent audit
7. ✅ Simulate rollback

### Production Deployment

```bash
# Start production API with all governance features
make run_prod_api

# Or use Docker Compose
docker-compose up -d
```

## 📚 Documentation

- **[GOVERNANCE_README.md](GOVERNANCE_README.md)** - Complete governance features documentation
- **[Makefile](Makefile)** - Build automation and deployment targets
- **[examples/golden_path_demo.py](examples/golden_path_demo.py)** - 30-minute production demo
- **[examples/governance_demo.py](examples/examples/governance_demo.py)** - Governance features demo

## 🏗️ Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Decision      │    │   Immutable     │    │   Legal         │
│   Functions     │───▶│   Trace Ledger  │───▶│   References    │
│   (Python/DSL)  │    │   (PostgreSQL)  │    │   (IRIs)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Release       │    │   Independent   │    │   Citizen       │
│   Management    │    │   Audit Service │    │   Explanation   │
│   (Signatures)  │    │   (Drift Det.)  │    │   API           │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Deterministic Execution

- **Time Semantics**: UTC normalization, timezone rules, clock skew handling
- **Feature Store**: Point-in-time lookups for replay consistency
- **Trace Schema**: Formal schema with versioning and migration support

## 🔧 Core Concepts

### Decision Functions

Decision functions are deterministic Python functions or DSL rules that take structured input and return structured output:

```python
from typing import Dict, Any
from decision_layer.core import DecisionContext
from decision_layer.time_semantics import DeterministicTime
from decision_layer.feature_store import feature_store

async def loan_eligibility_df(input_data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
    # Use deterministic time
    current_time = DeterministicTime.get_current_time()
    
    # Point-in-time feature lookup
    user_id = input_data.get("user_id", "user1")
    features = await feature_store.get_features_at_point_in_time(
        entity_id=user_id,
        feature_names=["user_credit_score", "loan_amount_limit"],
        as_of_timestamp=current_time
    )
    
    # Deterministic decision logic
    amount = input_data.get("amount", 0)
    credit_score = features.get("user_credit_score", {}).get("score", 0)
    
    if amount > 10000 and credit_score >= 700:
        return {"eligible": True, "reason": "High score, low amount"}
    else:
        return {"eligible": False, "reason": "Criteria not met"}
```

### DSL Rules

Formal rule-based DSL with conflict detection:

```yaml
rule_set_id: loan_eligibility_dsl
version: 1.0
description: DSL for loan eligibility

rules:
  - rule_id: rule_1_high_score_low_amount
    priority: 100
    conditions:
      - field: credit_score
        operator: ">="
        value: 700
      - field: amount
        operator: "<="
        value: 10000
    action:
      eligible: true
      reason: "Approved by DSL: High score, low amount"

  - rule_id: rule_2_default_deny
    priority: 10
    conditions: []
    action:
      eligible: false
      reason: "Default deny"
```

### Legal References

First-class legal linkage with validated IRIs:

```python
from decision_layer.legal_refs import create_legal_reference

legal_ref = create_legal_reference(
    system="finlex",
    act_id="544/1999",
    section="7",
    title="Consumer Protection Act, Section 7"
)
# Result: "https://finlex.fi/fi/laki/alkup/1999/19990544#L7"
```

### Release Management

Digital signatures with separation of duties:

```python
from decision_layer.release import ReleaseManager, SignerRole

# Create release
release_manager.create_release(
    function_id="loan_eligibility",
    version="1.0.0",
    legal_references=[legal_ref],
    change_summary="Initial release"
)

# Owner signs
release_manager.sign_release(
    function_id="loan_eligibility",
    version="1.0.0",
    signer_id="alice",
    role=SignerRole.OWNER
)

# Reviewer signs
release_manager.sign_release(
    function_id="loan_eligibility", 
    version="1.0.0",
    signer_id="bob",
    role=SignerRole.REVIEWER
)

# Activate release
release_manager.activate_release("loan_eligibility", "1.0.0")
```

## 🚀 Usage Examples

### Deploying a Decision Function

```bash
# Deploy Python function
curl -X POST "http://localhost:8000/functions/loan_eligibility/deploy" \
  -H "Content-Type: application/json" \
  -d '{
    "function_code": "async def decision_function(input_data, context): ...",
    "version": "1.0.0"
  }'

# Create and activate release
curl -X POST "http://localhost:8000/registry/loan_eligibility/1.0.0/release" \
  -H "Content-Type: application/json" \
  -d '{
    "legal_references": [{"system": "finlex", "act_id": "544/1999", "section": "7"}],
    "change_summary": "Initial release"
  }'
```

### Executing Decisions

```bash
# Execute decision function
curl -X POST "http://localhost:8000/functions/loan_eligibility/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {"user_id": "user1", "amount": 5000},
    "version": "1.0.0",
    "client_id": "app_a"
  }'
```

### Getting Decision Explanations

```bash
# Get human-readable explanation
curl "http://localhost:8000/explain/trace_12345"
```

### Running Audits

```bash
# Trigger independent audit
curl -X POST "http://localhost:8000/audit/run"

# Get latest audit report
curl "http://localhost:8000/audit/report/latest"
```

## 📊 Testing SLOs

### Coverage Requirements

- **100% Branch Coverage** - All decision paths must be tested
- **90% Mutation Score** - Mutation testing for boundary conditions
- **Contract Tests** - Schema compatibility validation

### Performance SLOs

- **P95 < 100ms** - 95th percentile response time
- **P99 < 500ms** - 99th percentile response time
- **Zero Critical Vulnerabilities** - Security requirements

## 🔍 Analytics Schema

### BigQuery DDL

```sql
CREATE TABLE `project.dataset.decision_logs` (
  trace_id STRING NOT NULL,
  schema_version STRING NOT NULL,
  function_id STRING NOT NULL,
  version STRING NOT NULL,
  df_hash STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  caller STRING NOT NULL,
  status STRING NOT NULL,
  input_json JSON,
  output_json JSON,
  prev_hash STRING,
  chain_hash STRING,
  signer STRING,
  legal_references JSON,
  feature_snapshot JSON,
  context_data JSON
)
PARTITION BY DATE(timestamp)
CLUSTER BY function_id, version, status
OPTIONS (
  partition_expiration_days = 2555,  -- 7 years
  description = "Decision execution logs with governance metadata"
);
```

### Canonical Queries

```sql
-- Daily decision summaries
SELECT 
  function_id,
  version,
  DATE(timestamp) as date,
  COUNT(*) as total_decisions,
  COUNTIF(status = 'success') as successful_decisions,
  AVG(TIMESTAMP_DIFF(timestamp, LAG(timestamp) OVER (PARTITION BY function_id ORDER BY timestamp), MILLISECOND)) as avg_processing_time_ms
FROM `project.dataset.decision_logs`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY function_id, version, date
ORDER BY date DESC, function_id;

-- Error rate analysis
SELECT 
  function_id,
  version,
  DATE(timestamp) as date,
  COUNT(*) as total_decisions,
  COUNTIF(status = 'error') as error_count,
  ROUND(COUNTIF(status = 'error') / COUNT(*) * 100, 2) as error_rate_percent
FROM `project.dataset.decision_logs`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY function_id, version, date
HAVING error_rate_percent > 1.0
ORDER BY error_rate_percent DESC;
```

## 🛠️ Makefile Targets

```bash
# Setup and installation
make setup          # Create virtual environment
make install        # Install dependencies
make install-dev    # Install development dependencies

# Testing and quality
make test           # Run all tests
make lint           # Run linter
make test-coverage  # Run tests with coverage
make mutation-test  # Run mutation tests

# Development
make run_api        # Start development API
make run_prod_api   # Start production API with governance
make demo           # Run governance demo
make golden_path_demo # Run 30-minute golden path demo

# Production
make deploy         # Deploy to production
make rollback       # Rollback deployment
make monitor        # Start monitoring dashboard

# Maintenance
make clean          # Clean up build artifacts
make format         # Format code
make docs           # Generate documentation
```

## 🔒 Security Features

### Per-Function RBAC

```python
# Function-level access control
rbac_config = {
    "loan_eligibility": {
        "owners": ["alice", "bob"],
        "reviewers": ["charlie", "diana"],
        "executors": ["app_a", "app_b"]
    }
}
```

### Dual Control

High-risk logic changes require multiple approvals:

```python
# Requires both owner AND reviewer signatures
if risk_level == "HIGH":
    require_dual_control = True
    required_signatures = [SignerRole.OWNER, SignerRole.REVIEWER]
```

### PII Handling

```python
# Automatic PII detection and redaction
pii_fields = ["ssn", "credit_card", "email"]
sanitized_trace = sanitize_pii(trace_data, pii_fields)
```

## 📈 Operational SLOs

### Latency Targets

- **P95 < 100ms** - Decision execution
- **P99 < 500ms** - Complex decisions
- **P99 < 5s** - Audit operations

### Reliability

- **99.9% Uptime** - Service availability
- **< 1% Error Rate** - Decision failures
- **< 5min Rollback** - Emergency rollback time

### Circuit Breakers

```python
# Automatic circuit breaking on high error rates
circuit_breaker_config = {
    "failure_threshold": 5,
    "recovery_timeout": 30,
    "half_open_max_calls": 3
}
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd policy_as_code

# Install development dependencies
make install-dev

# Run tests
make test

# Run linting
make lint

# Run golden path demo
make golden_path_demo
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See [GOVERNANCE_README.md](GOVERNANCE_README.md)
- **Examples**: Check [examples/](examples/) directory
- **Issues**: Report issues on GitHub
- **Golden Path**: Run `make golden_path_demo` for 30-minute walkthrough