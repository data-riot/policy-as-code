# Claude.md - Policy as Code Repository Guide

This document provides a comprehensive guide for working with Claude on the Policy as Code repository - a production-grade governance platform for managing decision logic as versioned, auditable, and governable software artifacts.

## 🎯 Project Overview

**Policy as Code** is a sophisticated governance platform that transforms decision logic into versioned, auditable software artifacts. It combines traditional policy management with cutting-edge agentic AI capabilities, creating a comprehensive "Policy as Code" system with enterprise-grade features.

### Key Capabilities

- **🔒 Immutable Trace Ledger** - Append-only ledger with hash-chaining and cryptographic integrity
- **📜 Legal Compliance** - First-class legal linkage with validated IRIs (Finlex/EUR-Lex)
- **✍️ Digital Signatures** - Change control with owner/reviewer signatures and separation of duties
- **🔍 Independent Audit** - Separate audit service for integrity verification and drift detection
- **🧠 Agentic AI** - LLM-powered reasoning, conversational interfaces, and workflow orchestration
- **📊 Deterministic Execution** - Time semantics and point-in-time feature store for replay consistency
- **🎯 Formal DSL** - Rule-based DSL with priorities, conflict detection, and static analysis
- **🌐 Cross-Domain Integration** - Knowledge graphs and ontologies for complex decision scenarios
- **🔄 Shadow Testing** - A/B testing capabilities for decision functions
- **⏰ Temporal Queries** - Time-based decision analysis and historical queries

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Agentic AI Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │     LLM     │  │Conversational│  │  Workflow   │        │
│  │ Integration │  │  Interface   │  │Orchestrator │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│              Core Governance Platform                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Decision  │  │   Immutable │  │   Legal     │        │
│  │   Functions │  │   Trace     │  │   References│        │
│  │   (Python/DSL)│  │   Ledger   │  │   (IRIs)   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Release   │  │Independent  │  │   Citizen   │        │
│  │ Management  │  │   Audit     │  │ Explanation │        │
│  │ (Signatures)│  │   Service   │  │     API     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### Actual Project Structure

```
policy-as-code/
├── decision_layer/           # Core platform modules
│   ├── core.py              # Decision engine and context
│   ├── api.py               # Main REST API
│   ├── agentic_api.py       # Agentic AI endpoints
│   ├── trace_ledger.py      # Immutable trace ledger
│   ├── legal_refs.py        # Legal reference validation
│   ├── release.py           # Release management & signatures
│   ├── audit_service.py     # Independent audit service
│   ├── explain.py           # Citizen explanation API
│   ├── llm_integration.py  # LLM-powered reasoning
│   ├── conversational_interface.py  # Natural language interface
│   ├── workflow_orchestration.py   # Self-managing workflows
│   ├── agent_performance_monitor.py # Performance monitoring
│   ├── dsl_formal.py        # Formal DSL with static analysis
│   ├── time_semantics.py    # Deterministic time handling
│   ├── feature_store.py     # Point-in-time feature store
│   └── ...                  # Additional modules
├── examples/                # Demonstration scripts
│   ├── golden_path_demo.py  # 30-minute production demo
│   ├── governance_demo.py   # Governance features demo
│   ├── agentic_demo.py     # Agentic AI capabilities demo
│   ├── approval_decision.yaml # YAML decision example
│   ├── test_policy/         # Example decision functions
│   │   └── v1.0.py         # Sample decision function
│   └── ...                 # Additional examples
├── docs/                    # Comprehensive documentation
│   ├── api.md              # API documentation
│   ├── architecture.md     # Architecture guide
│   ├── deployment.md       # Deployment guide
│   ├── agentic-ai.md      # Agentic AI capabilities
│   ├── governance.md      # Governance features
│   ├── development.md     # Development guide
│   ├── release-notes.md   # Release notes
│   └── ...                 # Additional docs
├── tests/                  # Test suite with SLO requirements
├── traces/                 # Trace data storage
├── dev-setup.sh            # Development setup script
├── run_api.py             # Development API server
├── run_production_api.py  # Production API server
├── run_agentic_demo.py    # Standalone agentic demo
├── Makefile               # Build automation
├── config.yaml            # Configuration file
├── docker-compose.yml     # Docker deployment
└── pyproject.toml         # Project configuration
```

## 🚀 Quick Start with Claude

### 1. Understanding the Codebase

When working with Claude on this repository, start by understanding the key components:

- **`decision_layer/`** - Core platform modules (25+ Python files)
- **`examples/`** - Demonstration scripts and golden path demos
- **`docs/`** - Comprehensive documentation (10+ markdown files)
- **`tests/`** - Test suite with SLO requirements
- **`traces/`** - Trace data storage
- **`dev-setup.sh`** - Development and setup script

### 2. Key Files to Reference

- **`README.md`** - Main project documentation
- **`docs/agentic-ai.md`** - Agentic AI capabilities documentation
- **`docs/governance.md`** - Governance features documentation
- **`docs/release-notes.md`** - Development release notes
- **`pyproject.toml`** - Project configuration and dependencies
- **`Makefile`** - Build automation and deployment targets
- **`config.yaml`** - Configuration file
- **`docker-compose.yml`** - Docker deployment configuration

### 3. Running Demos

```bash
# 30-minute golden path demo
make golden_path_demo

# Governance features demo
make demo

# Agentic AI capabilities demo
python3 run_agentic_demo.py

# Development API server
python3 run_api.py

# Production API server
python3 run_production_api.py
```

## 🔧 Development Workflow with Claude

### 1. Setting Up Development Environment

```bash
# Install dependencies and setup environment
make install

# Setup PostgreSQL database
make setup-db

# Run comprehensive test suite with SLOs
make test

# Run linting and type checking
make lint

# Format code
make format

# Start development API server
python3 run_api.py

# Or start production API server
python3 run_production_api.py
```

### 2. Key Development Patterns

#### Decision Functions
Decision functions are deterministic Python functions or DSL rules:

```python
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

#### DSL Rules
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
```

#### Agentic AI Integration
LLM-powered reasoning and conversational interfaces:

```python
from decision_layer.llm_integration import LLMIntegration, AgenticContext, ReasoningMode

# Create LLM integration
llm_integration = LLMIntegration(config, registry)

# Create agentic context
context = AgenticContext(
    citizen_id="CITIZEN_001",
    service_type="benefits_application",
    urgency_level="normal"
)

# Make autonomous decision
decision = await llm_integration.reason_about_decision(
    decision_function=my_function,
    input_data=input_data,
    context=context,
    reasoning_mode=ReasoningMode.AUTONOMOUS
)
```

### 3. Testing and Quality Assurance

The project has strict SLO requirements:

- **100% Branch Coverage** - All decision paths must be tested
- **90% Mutation Score** - Mutation testing for boundary conditions
- **Contract Tests** - Schema compatibility validation
- **Performance SLOs** - P95 < 100ms, P99 < 500ms

```bash
# Run comprehensive tests
make test

# Run tests with coverage
make test-coverage

# Run mutation tests
make mutation-test

# Run linting
make lint
```

## 📊 Working with Data and Analytics

### 1. Feature Store Integration

The platform includes a point-in-time feature store for deterministic execution:

```python
from decision_layer.feature_store import feature_store

# Get features at specific point in time
features = await feature_store.get_features_at_point_in_time(
    entity_id="user_123",
    feature_names=["credit_score", "income", "employment_status"],
    as_of_timestamp=datetime.now(timezone.utc)
)
```

### 2. Analytics Schema

The platform provides BigQuery/Snowflake DDL for analytics:

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
CLUSTER BY function_id, version, status;
```

## 🔒 Security and Compliance

### 1. Legal References

All decision functions must reference applicable law:

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

### 2. Digital Signatures

Releases require dual control (owner + reviewer signatures):

```python
from decision_layer.release import ReleaseManager, SignerRole

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
```

### 3. Immutable Trace Ledger

Every decision execution creates an immutable trace record:

```python
from decision_layer.trace_ledger import TraceLedger

# Create trace record
trace_record = TraceRecord(
    trace_id=uuid.uuid4(),
    df_id="loan_eligibility",
    version="1.0.0",
    df_hash=function_hash,
    timestamp=datetime.now(timezone.utc),
    caller="api_client",
    status=TraceStatus.SUCCESS,
    input_json=input_data,
    output_json=result,
    prev_hash=previous_hash,
    chain_hash=current_hash,
    signer="system"
)

# Append to ledger
await trace_ledger.append_trace(trace_record)
```

## 🤖 Agentic AI Capabilities

### 1. Conversational Interface

Natural language interaction with citizens:

```python
from decision_layer.conversational_interface import ConversationalInterface

# Process citizen message
response = await conversational_interface.process_citizen_message(
    message="I need help with my tax return",
    session_id="session_001",
    channel=ConversationChannel.WEB_CHAT,
    citizen_id="CITIZEN_001"
)
```

### 2. Workflow Orchestration

Self-managing workflow orchestration:

```python
from decision_layer.workflow_orchestration import WorkflowOrchestrator

# Define workflow
workflow = WorkflowDefinition(
    workflow_id="benefits_workflow",
    name="Benefits Application Workflow",
    tasks=[
        WorkflowTask(
            task_id="validate_application",
            name="Validate Application",
            task_type="decision_function",
            required_capabilities=["validation"],
            estimated_duration=5
        )
    ]
)

# Start workflow
execution_id = await orchestrator.start_workflow(workflow)
```

### 3. Performance Monitoring

Real-time agent performance analysis:

```python
from decision_layer.agent_performance_monitor import AgentPerformanceMonitor

# Record performance metric
await monitor.record_performance_metric(
    agent_id="benefits_agent",
    metric_type=PerformanceMetric.DECISION_ACCURACY,
    value=0.95
)

# Detect drift
drift_results = await monitor.detect_agent_drift("benefits_agent")
```

## 🚀 Deployment and Production

### 1. Configuration

The platform uses `config.yaml` for configuration:

```yaml
# Storage configuration
storage:
  backend: "postgresql"  # or "file"
  connection_string: "postgresql://decision_user:decision_password@postgres:5432/decision_layer"

# Security configuration
security:
  enable_auth: true
  api_key: "${DECISION_LAYER_API_KEY}"
  enable_rate_limiting: true
  enable_input_sanitization: true
  max_input_size: 1048576  # 1MB
  rate_limit_requests: 100
  rate_limit_window: 60

# API configuration
api:
  host: "0.0.0.0"
  port: 8000
  enable_docs: true
  enable_cors: true
```

### 2. Production Deployment

```bash
# Start production API server
python3 run_production_api.py

# Or use Docker Compose
docker-compose up -d

# Run performance benchmarks
make benchmark

# Run compliance audit
make audit
```

### 3. Environment Variables

```bash
export DECISION_LAYER_API_KEY="your-api-key"
export DATABASE_URL="postgresql://user:pass@host:port/db"
export SECRET_KEY="your-secret-key"
```

### 4. Health Checks

- `GET /health` - Comprehensive health check
- Database connectivity
- Plugin status
- Security configuration
- Governance service status

## 📚 Documentation and Resources

### 1. Key Documentation Files

- **`README.md`** - Main project overview and quick start
- **`docs/agentic-ai.md`** - Agentic AI capabilities
- **`docs/governance.md`** - Governance features
- **`docs/release-notes.md`** - Development release notes
- **`docs/`** - Detailed documentation
  - `api.md` - API documentation
  - `architecture.md` - Architecture guide
  - `deployment.md` - Deployment guide
  - `installation.md` - Installation guide
  - `quickstart.md` - Quick start guide
  - `configuration.md` - Configuration guide
  - `cli.md` - CLI documentation
  - `web-interface.md` - Web interface guide
  - `yaml-interface.md` - YAML interface guide
  - `troubleshooting.md` - Troubleshooting guide

### 2. Example Scripts

- **`examples/golden_path_demo.py`** - 30-minute production demo
- **`examples/governance_demo.py`** - Governance features demo
- **`examples/agentic_demo.py`** - Agentic AI capabilities demo
- **`examples/approval_decision.yaml`** - YAML decision example
- **`examples/refund_policy.py`** - Refund policy example
- **`examples/risk_assessment.py`** - Risk assessment example
- **`examples/yaml_decision_example.py`** - YAML decision processing
- **`run_agentic_demo.py`** - Standalone agentic demo

### 3. Makefile Targets

```bash
# Setup and installation
make install        # Install dependencies and setup environment
make setup-db       # Setup PostgreSQL database

# Testing and quality
make test           # Run comprehensive test suite with SLOs
make lint           # Run linting and type checking
make format         # Format code

# Development
make demo           # Run governance features demo
make golden_path_demo # Run 30-minute golden path demo

# Production
make benchmark      # Run performance benchmarks
make audit          # Run compliance audit
make rollback       # Rollback deployment

# Utilities
make clean          # Clean up environment
make help           # Show help message
```

## 🎯 Common Tasks with Claude

### 1. Adding New Decision Functions

When adding new decision functions with Claude:

1. **Define the function** with proper type hints and deterministic constraints
2. **Add legal references** for compliance
3. **Create tests** with 100% branch coverage
4. **Register the function** in the registry
5. **Create and sign releases** with dual control
6. **Add documentation** and examples

### 2. Implementing Agentic AI Features

When implementing agentic AI features:

1. **Define agent capabilities** and register agents
2. **Implement LLM integration** with proper error handling
3. **Create conversational interfaces** for citizen interaction
4. **Design workflows** with self-orchestration capabilities
5. **Add performance monitoring** and drift detection
6. **Ensure compliance** with legal and security requirements

### 3. Debugging and Troubleshooting

Common debugging approaches:

1. **Check trace ledger** for decision execution history
2. **Run audit service** for integrity verification
3. **Review performance metrics** for agent effectiveness
4. **Validate legal references** for compliance issues
5. **Check digital signatures** for release validation
6. **Monitor drift detection** for behavior changes

## 🔮 Future Development Areas

### 1. Advanced Agentic Features

- **Federated Learning** - Learn from multiple government agencies
- **Predictive Analytics** - Predict citizen needs and service demands
- **Cross-Border Coordination** - Coordinate with international agencies
- **Advanced Security** - Enhanced security for agentic operations

### 2. Enhanced Governance

- **Advanced Audit Capabilities** - More sophisticated audit patterns
- **Enhanced Legal Integration** - Deeper integration with legal systems
- **Improved Transparency** - Better citizen-facing explanations
- **Advanced Compliance** - More comprehensive compliance frameworks

### 3. Performance Optimization

- **Advanced Caching** - Intelligent caching strategies
- **Performance Tuning** - Optimize for specific use cases
- **Scalability Improvements** - Better horizontal scaling
- **Resource Optimization** - Efficient resource utilization

## 🔧 Project Structure Details

### Core Modules (`decision_layer/`)

- **`core.py`** - Decision engine, context, and plugin architecture
- **`api.py`** - Main REST API with governance features
- **`agentic_api.py`** - Agentic AI endpoints
- **`trace_ledger.py`** - Immutable trace ledger with PostgreSQL backend
- **`legal_refs.py`** - Legal reference validation (Finlex/EUR-Lex)
- **`release.py`** - Release management with digital signatures
- **`audit_service.py`** - Independent audit service
- **`explain.py`** - Citizen-facing explanation API
- **`llm_integration.py`** - LLM-powered reasoning
- **`conversational_interface.py`** - Natural language interface
- **`workflow_orchestration.py`** - Self-managing workflows
- **`agent_performance_monitor.py`** - Performance monitoring
- **`dsl_formal.py`** - Formal DSL with static analysis
- **`time_semantics.py`** - Deterministic time handling
- **`feature_store.py`** - Point-in-time feature store
- **`df_constraints.py`** - Decision function constraints
- **`schemas.py`** - Pydantic schemas
- **`errors.py`** - Custom exception classes
- **`security.py`** - Security configuration
- **`storage.py`** - Storage backend abstraction
- **`testing_slos.py`** - Testing SLO requirements
- **`auth.py`** - Authentication and authorization

### Development Files

- **`run_api.py`** - Development API server
- **`run_production_api.py`** - Production API server
- **`run_agentic_demo.py`** - Standalone agentic demo
- **`config.yaml`** - Configuration file
- **`docker-compose.yml`** - Docker deployment
- **`Dockerfile`** - Docker image definition
- **`Makefile`** - Build automation
- **`pyproject.toml`** - Project configuration
- **`requirements.txt`** - Production dependencies
- **`requirements-dev.txt`** - Development dependencies

## 🤝 Contributing Guidelines

When contributing to this repository with Claude:

1. **Follow the governance model** - All changes must be properly signed and audited
2. **Maintain SLO requirements** - Ensure 100% test coverage and performance targets
3. **Document thoroughly** - Add comprehensive documentation for new features
4. **Test extensively** - Include unit tests, integration tests, and performance tests
5. **Ensure compliance** - Maintain legal and security compliance
6. **Follow coding standards** - Use proper type hints, error handling, and logging
7. **Use the Makefile** - Leverage existing automation for consistency
8. **Update documentation** - Keep docs in sync with code changes

## 📞 Support and Resources

- **Documentation**: Comprehensive docs in `/docs` directory
- **Examples**: Working examples in `/examples` directory
- **API Reference**: Available at `http://localhost:8000/docs` when running
- **Issues**: Report issues on GitHub
- **Discussions**: Join discussions on GitHub

---

**Policy as Code** represents the future of governance - where decision logic becomes auditable, compliant, and intelligent software that can reason, learn, and adapt while maintaining full accountability and transparency.

This platform enables organizations to build truly intelligent government services that can perceive, reason, and act autonomously while maintaining the highest standards of governance, compliance, and citizen trust.

### Key Differentiators

- **Production-Ready**: Enterprise-grade architecture with comprehensive testing and monitoring
- **Governance-First**: Built-in legal compliance, audit trails, and digital signatures
- **Agentic AI**: Advanced AI capabilities for autonomous decision-making and citizen interaction
- **Developer-Friendly**: Comprehensive tooling, documentation, and automation
- **Scalable**: Designed for horizontal scaling and high-performance requirements
- **Compliant**: Built-in support for legal references, audit requirements, and regulatory compliance

The platform provides a solid foundation for building the future of government services with AI agents that can perceive, reason, and act autonomously while maintaining full accountability and compliance.
