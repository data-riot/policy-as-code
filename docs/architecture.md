# Decision Layer Architecture

## Overview

The Decision Layer provides a structured approach to managing business decision logic as versioned, testable functions with structured observability. It treats decisions as software artifacts that can be versioned, tested, and monitored with the same rigor applied to code, data, and models.

## 🏗️ System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Decision Layer                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Registry  │  │   Engine    │  │   Schemas   │        │
│  │             │  │             │  │             │        │
│  │ • Versioning│  │ • Execution │  │ • Validation│        │
│  │ • Metadata  │  │ • Tracing   │  │ • Types     │        │
│  │ • Search    │  │ • Plugins   │  │ • Constraints│       │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│              Cross-Domain Communication                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │     LLM     │  │  Ontology   │  │ Knowledge   │        │
│  │ Integration │  │ Integration │  │   Graph     │        │
│  │             │  │             │  │ Integration │        │
│  │ • Code Gen  │  │ • Schema Gen│  │ • Context   │        │
│  │ • Explain   │  │ • Validation│  │ • Traces    │        │
│  │ • Query     │  │ • Enrich    │  │ • Analysis  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                    Interfaces                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │     CLI     │  │     API     │  │     Web     │        │
│  │             │  │             │  │             │        │
│  │ • Commands  │  │ • REST      │  │ • Streamlit │        │
│  │ • Scripts   │  │ • FastAPI   │  │ • Dashboard │        │
│  │ • Batch     │  │ • Async     │  │ • Visual    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Core Components

### 1. Schema Validation System

**Purpose**: Ensures type safety and data integrity for decision inputs and outputs.

**Key Components**:
- `SchemaField`: Defines field types, constraints, and validation rules
- `DecisionSchema`: Complete schema definition for input/output validation
- `SchemaValidator`: Runtime validation engine with comprehensive type checking

**Features**:
- **Type Support**: String, Integer, Float, Boolean, DateTime, Object, Array, Enum
- **Constraints**: Min/max values, enums, patterns, required/optional fields
- **Nested Objects**: Support for complex nested data structures
- **Custom Validators**: User-defined validation functions
- **Error Reporting**: Detailed validation error messages with field paths

**Example Usage**:
```python
from decision_layer.schemas import DecisionSchema, SchemaField, FieldType

schema = DecisionSchema(
    input_schema={
        "user_id": SchemaField(name="user_id", type=FieldType.INTEGER, required=True),
        "amount": SchemaField(name="amount", type=FieldType.FLOAT, min_value=0.0),
        "product": SchemaField(
            name="product", 
            type=FieldType.ENUM, 
            enum_values=["loan", "credit", "insurance"]
        )
    },
    output_schema={
        "approved": SchemaField(name="approved", type=FieldType.BOOLEAN, required=True),
        "reason": SchemaField(name="reason", type=FieldType.STRING, required=True)
    }
)
```

### 2. Function Registry

**Purpose**: Centralized management of versioned decision functions with rich metadata and governance.

**Key Components**:
- `FunctionRegistry`: Central registry with versioning and search capabilities
- `FunctionMetadata`: Rich metadata including author, tags, policy references
- `FunctionArtifact`: Complete function definition with logic, schema, and metadata

**Features**:
- **Immutable Versioning**: Each function version is stored immutably
- **Semantic Versioning**: Support for semantic (v1.2.3) and simple (v3.2) versions
- **Rich Metadata**: Author, description, tags, policy references, compliance requirements
- **Governance Workflows**: DRAFT → REVIEW → APPROVED → DEPRECATED → ARCHIVED
- **Search & Discovery**: Find functions by tags, author, or other criteria
- **Lineage Tracking**: Complete history and dependency tracking

**Example Usage**:
```python
from decision_layer.registry import FunctionRegistry, FunctionStatus

registry = FunctionRegistry("./registry")

artifact = registry.register_function(
    function_id="loan_approval",
    version="1.0",
    logic_code=function_code,
    schema=schema,
    metadata={
        "title": "Loan Approval Policy",
        "description": "Approves loans based on credit score and income",
        "author": "finance-team",
        "tags": ["loan", "approval", "finance"],
        "policy_references": ["POL-001", "POL-002"],
        "compliance_requirements": ["SOX", "GDPR"]
    },
    status=FunctionStatus.DRAFT
)
```

### 3. Decision Engine

**Purpose**: Deterministic, traceable execution of decision functions with comprehensive error handling and plugin support.

**Key Features**:
- **Schema Validation**: Optional input/output validation
- **Deterministic Execution**: Guaranteed reproducible results
- **Structured Tracing**: Comprehensive execution traces with hashes
- **Plugin Architecture**: Extensible with validation, tracing, and caching plugins
- **Error Handling**: Graceful error handling with detailed error traces
- **Performance Monitoring**: Execution time tracking
- **Security**: Input sanitization and rate limiting

**Example Usage**:
```python
from decision_layer.core import DecisionEngine

engine = DecisionEngine()

result = await engine.execute(
    function_id="loan_approval",
    input_data={"user_id": 123, "amount": 5000, "credit_score": 750},
    version="1.0"
)
```

### 4. Shadow Runner

**Purpose**: Safe testing of decision logic without affecting production decisions.

**Key Components**:
- `ShadowRunner`: Engine for running shadow analysis
- `ShadowResult`: Detailed comparison results between versions

**Features**:
- **Simulation Mode**: Test new versions against historical inputs
- **Mirror Mode**: Run both versions in parallel on live traffic
- **Regression Analysis**: Categorize differences as regressions, improvements, or neutral changes
- **Comprehensive Reporting**: Detailed analysis with confidence scores

**Example Usage**:
```python
from decision_layer.shadow_runner import ShadowRunner

shadow_runner = ShadowRunner(registry)

# Run simulation
results = await shadow_runner.run_simulation(
    function_id="loan_approval",
    current_version="1.0",
    shadow_version="2.0",
    inputs=historical_inputs
)

# Analyze for regressions
analysis = await shadow_runner.analyze_regression(
    function_id="loan_approval",
    current_version="1.0",
    shadow_version="2.0",
    inputs=test_inputs
)
```

## 🌐 Cross-Domain Communication

### 1. LLM Integration

**Capabilities**:
- **Natural Language to Code Generation**: Convert policy descriptions to decision functions
- **Decision Function Explanation**: Generate natural language explanations for any audience
- **Natural Language Query Processing**: Answer questions about decisions in plain English
- **Policy Documentation Generation**: Create comprehensive documentation from functions

**Example Usage**:
```python
from decision_layer.llm_integration import LLMIntegration

llm_integration = LLMIntegration(registry, llm_provider)

# Generate decision function from natural language
artifact = await llm_integration.generate_decision_function(
    policy_description="Approve loans for users with credit score > 700 and income > $50,000",
    function_id="loan_approval_llm",
    version="1.0"
)

# Explain decision function for different audiences
explanation = await llm_integration.explain_decision_function(
    function_id="loan_approval",
    audience="user",  # user, business, technical
    format="natural"  # natural, structured, code
)
```

### 2. Ontology Integration

**Capabilities**:
- **Ontology-Driven Schema Generation**: Create schemas from ontology classes
- **Semantic Validation**: Validate data against ontological definitions
- **Context Enrichment**: Enhance data with ontological relationships
- **Schema Mapping**: Bidirectional mapping between ontologies and schemas

**Example Usage**:
```python
from decision_layer.ontology_integration import OntologyIntegration

ontology_integration = OntologyIntegration(ontology_provider)

# Create schema from ontology
schema = ontology_integration.create_schema_from_ontology("Patient")

# Validate data against ontology
validation = ontology_integration.validate_with_ontology(patient_data, "Patient")

# Enrich data with ontological context
enriched = ontology_integration.enrich_with_ontology(
    patient_data, "Patient", include_relationships=True
)
```

### 3. Knowledge Graph Integration

**Capabilities**:
- **Context Enrichment**: Enhance decisions with KG entity relationships
- **Trace Storage**: Store decision traces as graph nodes and relationships
- **Risk Analysis**: Analyze entity risk using graph relationships
- **Decision History**: Query decision history through graph traversals

**Example Usage**:
```python
from decision_layer.knowledge_graph_integration import KnowledgeGraphIntegration

kg_integration = KnowledgeGraphIntegration(kg_provider, registry)

# Enrich decision context with KG data
context = await kg_integration.enrich_decision_context("user_123", "User")

# Store decision trace in knowledge graph
trace = await kg_integration.store_decision_trace(trace_data, ["user_123"])

# Analyze entity risk using KG
risk_analysis = await kg_integration.analyze_entity_risk("user_123", "User")
```

### 4. Unified Natural Language Interface

**Capabilities**:
- **Single Point of Interaction**: Unified interface for all stakeholders
- **Cross-Domain Query Processing**: Process queries using all available knowledge sources
- **Multi-Format Explanations**: Generate explanations in various formats
- **Comprehensive Reporting**: Create reports integrating all domains

**Example Usage**:
```python
from decision_layer.natural_language_interface import UnifiedNaturalLanguageInterface

interface = UnifiedNaturalLanguageInterface(
    registry=registry,
    engine=engine,
    llm_integration=llm_integration,
    ontology_integration=ontology_integration,
    knowledge_graph_integration=kg_integration
)

# Process queries with cross-domain enrichment
response = await interface.process_query(
    query="What are the risk factors for user 123?",
    include_cross_domain=True
)

# Generate comprehensive reports
report = await interface.generate_report({
    "function_id": "loan_approval",
    "time_range": {"start": "2025-01-01", "end": "2025-01-31"}
})
```

## 🔌 Plugin Architecture

The Decision Layer uses a plugin architecture for extensibility:

### Plugin Types
- **Validation Plugins**: Custom input/output validation
- **Tracing Plugins**: Custom trace storage and analysis
- **Caching Plugins**: Custom caching strategies
- **Security Plugins**: Custom security and access control

### Example Plugin
```python
from decision_layer.core import DecisionPlugin

class CustomValidationPlugin(DecisionPlugin):
    async def process(self, data: Dict[str, Any], context: DecisionContext) -> Dict[str, Any]:
        # Custom validation logic
        return data
    
    @property
    def name(self) -> str:
        return "custom_validation"
```

## 🚀 Interfaces

### 1. Command Line Interface (CLI)
- **Deploy functions**: `decision-layer deploy function_id version function_file`
- **Execute decisions**: `decision-layer execute function_id input_file`
- **List functions**: `decision-layer list`
- **View traces**: `decision-layer traces function_id`

### 2. REST API
- **FastAPI-based**: Auto-generated documentation
- **Async support**: High-performance concurrent execution
- **OpenAPI spec**: Complete API specification
- **Authentication**: API key and Bearer token support

### 3. Web Interface
- **Streamlit-based**: Interactive web dashboard
- **Visual function editor**: Drag-and-drop interface
- **Trace viewer**: Interactive trace analysis
- **Configuration management**: Web-based configuration

## 🔒 Security & Compliance

### Security Features
- **Input Sanitization**: Automatic sanitization of sensitive data
- **Rate Limiting**: Configurable rate limiting per client
- **Authentication**: API key and token-based authentication
- **Audit Logging**: Comprehensive audit trails

### Compliance Features
- **Data Lineage**: Complete data lineage tracking
- **Policy References**: Link decisions to policy documents
- **Compliance Requirements**: Track regulatory requirements
- **Audit Trails**: Immutable audit logs for compliance

## 📊 Observability

### Tracing
- **Structured Traces**: JSON-formatted trace data
- **Input/Output Hashing**: Cryptographic hashing for privacy
- **Performance Metrics**: Execution time and resource usage
- **Error Tracking**: Detailed error information

### Monitoring
- **Metrics Collection**: Decision execution metrics
- **Alerting**: Configurable alerts for anomalies
- **Dashboards**: Pre-built monitoring dashboards
- **Integration**: Prometheus, Grafana, and other monitoring tools

## 🎯 Design Principles

1. **Determinism**: All decisions are deterministic and reproducible
2. **Versioning**: Every change is versioned and immutable
3. **Observability**: Complete visibility into decision execution
4. **Extensibility**: Plugin architecture for custom functionality
5. **Security**: Built-in security and compliance features
6. **Cross-Domain**: Seamless integration across different knowledge representations
7. **Production-Ready**: Enterprise-grade reliability and performance

This architecture provides a robust foundation for managing decision logic with the same rigor applied to other software artifacts, while enabling innovative cross-domain communication capabilities. 