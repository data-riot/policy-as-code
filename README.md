# Policy as Code - Open Standard for Agentic State

> **Open standard for Agentic State, where every automated decision is bound to law, signed and explainable.** Decision Engineering reference code of lawful, auditable and explainable automation. Turning policy and legislation into executable, accountable Decision Functions.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 **Get Started in 5 Minutes**

```bash
# Clone and install
git clone https://github.com/your-org/policy-as-code.git
cd policy-as-code
pip3 install -r requirements.txt
pip3 install -e .

# Run your first decision
python3 examples/simple_demo.py
```

**That's it!** You now have a working Policy as Code system. 🎉

---

## 🎯 **What is Agentic State?**

**Agentic State** represents the next evolution in governance: autonomous decision-making systems that operate within strict legal boundaries while maintaining full accountability and explainability.

This platform implements **Decision Engineering** - an operational architecture that connects legislation, automated decision logic, and audit evidence. Every automated decision is represented as a **Decision Function (DF)** - a formally described, signed, and auditable unit of logic linked directly to its legal section.

### **Core Principles**

- 🔒 **Bound to Law** - Every decision function is directly linked to legal references (Finlex/EUR-Lex IRIs)
- ✍️ **Signed & Accountable** - Digital signatures with separation of duties and immutable audit trails
- 🔍 **Explainable** - Citizen-facing explanations with decision paths and legal basis
- 🧠 **Agentic** - LLM-powered reasoning, conversational interfaces, and autonomous workflows
- 🌐 **Cross-Border** - EU-wide deployment with Nordic-Baltic pioneer implementation

### **Decision Function Architecture**

```python
DecisionFunction(
    id: string,
    version: semver,
    law_reference: URI,           # Direct link to Finlex/EUR-Lex section
    owner: ministry_id,
    inputs_schema: JSON Schema,
    outputs_schema: JSON Schema,
    logic_hash: SHA256,           # Cryptographic integrity
    signatures: [owner_sign, reviewer_sign]  # Separation of duties
)
```

This makes law executable without losing human accountability.

### **Legal Binding in Action**

Every Decision Function is bound to specific legal sections:

```python
# Healthcare eligibility function
def healthcare_eligibility(patient_data):
    """Healthcare eligibility based on Patient Safety Act Section 3"""
    # Legal reference: https://finlex.fi/fi/laki/alkup/2010/20100580#L3
    # EU AI Act compliance: High-risk medical device system

    if patient_data.age < 18 and procedure.requires_adult_consent:
        return {
            "eligible": False,
            "reason": "Requires adult consent per Patient Safety Act",
            "legal_basis": "https://finlex.fi/fi/laki/alkup/2010/20100580#L3",
            "requires_human_review": True
        }
```

**Key Legal Features:**
- **Direct IRI Links**: Every function links to specific Finlex/EUR-Lex sections
- **Section-Level Granularity**: References specific subsections, not entire laws
- **EU AI Act Compliance**: Built-in compliance for high-risk AI systems
- **Required Legal References**: Functions cannot be deployed without valid legal basis

### **Production-Grade Governance**

**Digital Signatures & Change Control:**
- **Separation of Duties**: Owner + reviewer signatures required
- **Release State Machine**: draft → pending → approved → active
- **Activation Gates**: Prevents execution of unsigned functions
- **Audit Trail**: Complete signature event history

**Immutable Trace Ledger:**
- **Hash-Chained**: SHA-256 cryptographic integrity
- **Append-Only**: Tamper-proof decision history
- **Independent Audit**: Separate service for integrity verification
- **Drift Detection**: Automatic detection of decision pattern changes

**Citizen-Facing Explanation API:**
- **Human-Readable Justifications**: Clear decision reasoning
- **Legal Basis**: Direct links to regulations
- **Decision Path**: Step-by-step reasoning process
- **Privacy Controls**: Field redaction for sensitive data

### **EU AI Act Compliance & Cross-Border Architecture**

**EU AI Act Compliance:**
- **High-Risk Systems**: Healthcare, immigration, social benefits with full compliance
- **Bias Detection**: Active monitoring for protected characteristics
- **Human Oversight**: Required for critical decisions
- **Prohibited Practices**: Complete avoidance of banned AI practices
- **Transparency**: Clear decision methodology and appeal processes

**Cross-Border Architecture:**
- **EU AI Commons Vision**: Shared infrastructure across European Union countries
- **Nordic-Baltic Pioneer**: First implementation region with multilingual support
- **Cross-Border APIs**: Seamless data exchange between countries
- **Shared Decision Functions**: Common policies and legal frameworks
- **Multilingual AI**: Native language models for Nordic-Baltic languages

---

## 🎓 **Learn Step by Step**

**📖 [Complete Getting Started Guide](GETTING_STARTED.md)** - Everything you need to know

### **Quick Learning Path**
1. **Level 1** (15 min): `python3 examples/level1_basic_approval.py`
2. **Level 2** (30 min): `python3 examples/level1_loan_approval.py`
3. **Level 3** (45 min): Explore `examples/demos/` for real applications
4. **Level 4** (60 min): Use APIs for production systems

---

## 🏗️ **How It Works**

### **1. Write Your Business Logic**
```python
def loan_approval(input_data):
    """Simple loan approval logic"""
    credit_score = input_data.get("credit_score", 0)
    income = input_data.get("income", 0)

    if credit_score >= 700 and income >= 50000:
        return {"approved": True, "amount": min(income * 3, 500000)}
    else:
        return {"approved": False, "reason": "Criteria not met"}
```

### **2. Deploy and Execute**
```bash
# Deploy your function
policy-as-code deploy loan_approval 1.0 loan_approval.py

# Execute with real data
echo '{"credit_score": 750, "income": 75000}' | policy-as-code execute loan_approval
```

### **3. Get Automatic Benefits**
- ✅ **Input Validation** - Automatic data validation
- ✅ **Output Validation** - Consistent response format
- ✅ **Audit Trail** - Every decision is logged
- ✅ **Legal Compliance** - Built-in legal references
- ✅ **Performance Monitoring** - Real-time metrics

---

## 🎯 **Real-World Use Cases**

### **Government & Public Sector**
- **Social Benefits** - Automated welfare eligibility
- **Tax Calculation** - Complex tax computations
- **Immigration** - Visa processing workflows
- **Healthcare** - Medical procedure eligibility

### **Financial Services**
- **Loan Approval** - Credit risk assessment
- **Insurance** - Policy underwriting
- **Compliance** - Regulatory requirement checking
- **Fraud Detection** - Risk scoring algorithms

### **Business Operations**
- **HR Policies** - Employee benefit calculations
- **Pricing Rules** - Dynamic pricing logic
- **Approval Workflows** - Multi-step decision processes
- **Compliance** - Regulatory requirement validation

---

## 🚀 **Key Features**

### **🔒 Immutable Audit Trail**
Every decision is cryptographically signed and stored in an append-only ledger.

### **📜 Legal Compliance**
Built-in support for legal references (Finlex, EUR-Lex) and EU AI Act compliance.

### **🧠 AI-Powered Reasoning**
LLM integration for complex decision-making and natural language explanations.

### **📊 Performance Monitoring**
Real-time metrics, alerting, and comprehensive analytics.

### **🔌 Multiple APIs**
REST, GraphQL, WebSocket, and Python SDK for any integration need.

---

## 🏛️ **Agentic State Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    Agentic State Platform                   │
├─────────────────────────────────────────────────────────────┤
│ • Decision Engine     • Immutable Trace Ledger             │
│ • Legal Compliance    • Digital Signatures                 │
│ • Agentic AI         • Performance Monitoring             │
│ • Multiple APIs       • Audit & Governance                 │
│ • Cross-Border       • EU AI Commons                      │
└─────────────────────────────────────────────────────────────┘
```

### **Four-Layer Architecture**

| Layer | Function | Owner |
|-------|----------|-------|
| **Normative Layer** | Law text and legislative metadata (Finlex ELI) | Legal Register Centre |
| **Model Layer** | Decision Functions with formal schemas and logic | Legal Engineering Office |
| **Execution Layer** | Systems and agents calling DFs via APIs | Agencies |
| **Integrity Layer** | Immutable Trace Ledger and Audit Service | Audit & Integrity Agency |

### **Agentic AI Capabilities**

- **🧠 LLM-Powered Reasoning**: Autonomous decision-making with full reasoning chains
- **💬 Conversational Interface**: Natural language interaction with citizens
- **🔄 Workflow Orchestration**: Self-managing government workflows
- **📊 Performance Monitoring**: Real-time agent performance analysis
- **🤝 Multi-Agent Coordination**: Intelligent coordination between AI agents
- **🔍 Drift Detection**: Automatic detection of agent behavior changes

---

## 🎯 **Quick Start Examples**

### **Example 1: Simple Loan Approval**
```python
def loan_approval(data):
    return {
        "approved": data.credit_score >= 700 and data.income >= 50000,
        "amount": min(data.income * 3, 500000) if data.credit_score >= 700 else 0
    }
```

### **Example 2: Healthcare Eligibility**
```python
def healthcare_eligibility(data):
    patient = data.patient
    procedure = data.procedure

    if patient.age < 18 and procedure.requires_adult_consent:
        return {"eligible": False, "reason": "Requires adult consent"}

    if not data.insurance.covers_procedure:
        return {"eligible": False, "reason": "Not covered by insurance"}

    return {"eligible": True, "estimated_cost": procedure.base_cost}
```

### **Example 3: Tax Calculation**
```python
def tax_calculation(data):
    income = data.income
    brackets = [(0, 11000, 0.10), (11000, 44725, 0.12), ...]

    tax = 0
    for min_income, max_income, rate in brackets:
        if income > min_income:
            bracket_income = min(income, max_income) - min_income
            tax += bracket_income * rate

    return {"taxable_income": income, "total_tax": tax}
```

---

## 🚀 **Get Started Now**

### **Option 1: Quick Start** (5 minutes)
```bash
git clone https://github.com/your-org/policy-as-code.git
cd policy-as-code
pip3 install -r requirements.txt
pip3 install -e .
python3 examples/simple_demo.py
```

### **Option 2: Learn Step by Step** (2 hours)
1. **Level 1**: `python3 examples/level1_basic_approval.py`
2. **Level 2**: `python3 examples/level1_loan_approval.py`
3. **Level 3**: Check out `examples/demos/` for real applications
4. **Level 4**: Use the API for production systems

### **Option 3: Build Something Real** (1 hour)
1. **API Guide**: Use REST/GraphQL APIs
2. **Real Examples**: Healthcare, tax, immigration examples
3. **Deployment**: Production-ready systems

---

## 🆘 **Need Help?**

- **Getting Started**: [Complete Guide](GETTING_STARTED.md)
- **Architecture**: [System Overview](ARCHITECTURE_OVERVIEW.md)
- **Questions**: Open a GitHub issue
- **Contributing**: See [Contributing Guide](CONTRIBUTING.md)

---

## 📚 **Documentation**

- **[Getting Started Guide](GETTING_STARTED.md)** - Complete learning path
- **[Architecture Overview](ARCHITECTURE_OVERVIEW.md)** - System design
- **[API Reference](docs/reference/api.md)** - Complete API docs
- **[Deployment Guide](docs/getting-started/deployment.md)** - Production deployment
- **[Full Documentation](docs/)** - Complete reference

---

## 🤝 **Contributing**

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

### **Quick Contribution Setup**
```bash
git clone https://github.com/your-org/policy-as-code.git
cd policy-as-code
pip3 install -r requirements-dev.txt
make test
make lint
```

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 **Why Agentic State?**

**We're building the future of accountable automation.**

Agentic State represents the next evolution in governance - autonomous decision-making systems that operate within strict legal boundaries while maintaining full accountability and explainability.

- **✅ Law-Bound Automation** - Every decision directly linked to legal references
- **✅ Production-Grade Governance** - Digital signatures, audit trails, and drift detection
- **✅ EU AI Act Compliant** - Built-in compliance for high-risk AI systems
- **✅ Agentic AI** - LLM-powered reasoning and conversational interfaces
- **✅ Cross-Border Ready** - EU AI Commons vision with Nordic-Baltic pioneer implementation
- **✅ Open Standard** - MIT licensed reference implementation

**Ready to transform governance with accountable automation?** [Get started now!](#-get-started-in-5-minutes) 🚀

---

*Built with ❤️ for the future of accountable automation*
