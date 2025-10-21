# Policy as Code - Production Governance Platform

A production-grade agentic governance platform with immutable trace ledger, legal compliance, digital signatures, and independent audit capabilities.

## Production-Grade Governance Features

### 1. Immutable Trace Ledger
- **Hash-chained append-only ledger** with PostgreSQL backend
- **Cryptographic integrity** with SHA256 chain hashing
- **Signer identity** and timestamp verification
- **Queryable audit trail** for compliance and investigations

### 2. Legal Reference Validation
- **First-class legal linkage** with validated IRIs
- **Finlex/EUR-Lex integration** for Finnish and EU law
- **Required legal references** for all decision functions
- **Section-level granularity** with subsection support

### 3. Digital Signatures & Change Control
- **Separation of duties** (owner + reviewer signatures required)
- **Release state machine** (draft → pending → approved → active)
- **Activation gates** preventing execution of unsigned functions
- **Audit trail** of all signature events

### 4. Citizen-Facing Explanation API
- **Human-readable justifications** for all decisions
- **Legal basis** with direct links to regulations
- **Decision path** showing reasoning steps
- **Privacy controls** with field redaction

### 5. Independent Audit Service
- **Trace verification** against function hashes
- **Chain integrity** validation
- **Replay testing** for consistency
- **Drift detection** for decision pattern changes
- **Daily integrity reports** with failure counts

### 6. Deterministic Function Constraints
- **@df_pure decorator** for deterministic functions
- **Static analysis** banning network/IO/randomness
- **DSL transpiler** for rule-based functions
- **Compilation validation** before execution

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Decision      │    │   Trace         │    │   Release      │
│   Engine        │───▶│   Ledger        │    │   Manager      │
│                 │    │   (PostgreSQL)  │    │   (Signatures) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Explanation   │    │   Audit         │    │   Legal         │
│   API           │    │   Service       │    │   References    │
│   (Citizen)     │    │   (Independent)│    │   (IRI Valid)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database
```bash
# PostgreSQL setup
createdb policy_as_code
export DATABASE_URL="postgresql://postgres:password@localhost:5432/policy_as_code"
```

### 3. Run Production API
```bash
python run_production_api.py
```

### 4. Access API Documentation
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Core Decision Execution
- `POST /functions/{function_id}/execute` - Execute decision function
- `GET /functions` - List available functions
- `POST /functions/{function_id}/deploy` - Deploy new function

### Governance Features
- `GET /explain/{trace_id}` - Get citizen-facing explanation
- `GET /audit/report/latest` - Get latest audit report
- `POST /audit/run` - Run integrity audit
- `POST /legal/validate` - Validate legal reference

### Release Management
- `POST /registry/{function_id}/{version}/release` - Create release
- `POST /registry/{function_id}/{version}/sign` - Sign release
- `POST /registry/{function_id}/{version}/activate` - Activate release
- `GET /registry/{function_id}/{version}/release` - Get release info

## Security & Compliance

### Immutable Audit Trail
Every decision execution creates an immutable trace record:
```json
{
  "trace_id": "uuid",
  "df_id": "loan_approval",
  "version": "1.0",
  "df_hash": "sha256_hash",
  "timestamp": "2024-01-15T10:30:00Z",
  "caller": "api_client",
  "status": "success",
  "input_json": {...},
  "output_json": {...},
  "prev_hash": "previous_chain_hash",
  "chain_hash": "current_chain_hash",
  "signer": "system"
}
```

### Legal Compliance
All decision functions must reference applicable law:
```python
legal_refs = [
    LawReference(
        system=LegalSystem.EURLEX,
        act_id="32016R0679",  # GDPR
        title="General Data Protection Regulation"
    )
]
```

### Digital Signatures
Releases require two signatures:
```python
# Owner signature
release_manager.sign_release(
    function_id="loan_approval",
    version="1.0",
    signer_id="john.doe",
    role=SignerRole.OWNER
)

# Reviewer signature
release_manager.sign_release(
    function_id="loan_approval",
    version="1.0",
    signer_id="jane.smith",
    role=SignerRole.REVIEWER
)
```

## Deterministic Functions

### Pure Function Decorator
```python
@df_pure
def approval_decision(input_data, context):
    """Deterministic loan approval function"""
    amount = input_data.get("amount", 0)
    credit_score = input_data.get("credit_score", 0)

    approved = amount <= 100000 and credit_score >= 650

    return {
        "approved": approved,
        "confidence": 0.95,
        "decision_date": "2024-01-15"  # Fixed for determinism
    }
```

### DSL Rule Transpiler
```yaml
name: approval_decision
rules:
  - type: threshold
    field: amount
    threshold: 100000
    operator: "<="
    output_field: amount_approved
  - type: threshold
    field: credit_score
    threshold: 650
    operator: ">="
    output_field: score_approved
```

## Audit & Monitoring

### Daily Integrity Checks
- **Hash verification** of all traces
- **Chain integrity** validation
- **Replay testing** for consistency
- **Drift detection** for decision patterns
- **Signature verification** for releases

### Audit Report Example
```json
{
  "report_id": "audit_20240115_103000",
  "generated_at": "2024-01-15T10:30:00Z",
  "audit_status": "completed",
  "total_traces": 1250,
  "checked_traces": 1250,
  "failed_checks": 0,
  "drift_count": 0,
  "summary": "All integrity checks passed"
}
```

## 🌍 Citizen-Facing Explanations

### Explanation API Response
```json
{
  "trace_id": "trace_123",
  "decision": "Loan approved based on credit score and income",
  "legal_basis": [
    {
      "system": "eurlex",
      "act_id": "32016R0679",
      "title": "General Data Protection Regulation",
      "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679"
    }
  ],
  "decision_path": [
    "Applied decision function: loan_approval v1.0",
    "Analyzed amount: 50000",
    "Evaluated credit score: 750",
    "Applied business rules and compliance checks"
  ],
  "confidence_score": 0.95,
  "redacted_fields": ["customer_id"]
}
```

## Production Deployment

### Environment Variables
```bash
export DATABASE_URL="postgresql://user:pass@host:port/db"
export SECRET_KEY="changeme-secret-key"
export AUDIT_INTERVAL_HOURS="24"
export ENABLE_RATE_LIMITING="true"
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run_production_api.py"]
```

### Health Checks
- `GET /health` - Comprehensive health check
- Database connectivity
- Plugin status
- Security configuration
- Governance service status

## Monitoring & Observability

### Metrics
- Decision execution count
- Trace ledger size
- Audit failure rate
- Signature verification success
- Legal reference validation rate

### Alerts
- Chain integrity failures
- Missing signatures
- Legal reference violations
- Determinism constraint breaches
- Audit service failures

## Development

### Running Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Type checking
mypy policy_as_code/

# Linting
flake8 policy_as_code/

# Security scanning
bandit -r policy_as_code/
```

### Demo Script
```bash
python examples/governance_demo.py
```

## Documentation

- [API Documentation](docs/api.md)
- [Architecture Guide](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Security Guide](docs/security.md)
- [Compliance Guide](docs/compliance.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all governance constraints pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: GitHub Issues
- **Documentation**: `/docs` directory
- **Examples**: `/examples` directory
- **API Reference**: http://localhost:8000/docs

---

**Production-Ready Agentic Governance Platform**
*Immutable • Auditable • Compliant • Transparent*
