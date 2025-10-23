# Policy as Code - Transform Business Rules into Executable Software

> **Turn your business decisions into versioned, auditable code** - with legal compliance, audit trails, and AI-powered reasoning.

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

## 🎯 **What is Policy as Code?**

Policy as Code transforms business rules into executable, auditable software. Think of it as **"Git for business decisions"** - every decision is:

- ✅ **Versioned** - Track changes over time
- ✅ **Signed** - Digital signatures for approval
- ✅ **Auditable** - Complete decision history
- ✅ **Compliant** - Built-in legal references
- ✅ **Testable** - Automated testing and validation

### **Real-World Example**

Instead of this manual process:
```
❌ Manual: "Check if income > $50k and credit score > 700"
❌ Manual: "Write decision in Word document"
❌ Manual: "Email to manager for approval"
❌ Manual: "Store in filing cabinet"
```

You get this automated process:
```python
✅ Code: def loan_approval(data):
✅ Code:   return {"approved": data.income > 50000 and data.credit_score > 700}
✅ Code: # Automatically versioned, signed, and audited
```

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

## 🏛️ **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    Policy as Code Platform                  │
├─────────────────────────────────────────────────────────────┤
│ • Decision Engine     • Immutable Trace Ledger             │
│ • Legal Compliance    • Digital Signatures                 │
│ • AI Integration      • Performance Monitoring             │
│ • Multiple APIs       • Audit & Governance                 │
└─────────────────────────────────────────────────────────────┘
```

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

## 🌟 **Why Policy as Code?**

**We're building the future of business decision-making.**

Policy as Code represents the next evolution in how organizations handle business rules - from manual, error-prone processes to automated, auditable, and intelligent decision-making systems.

- **✅ Production-Ready Foundation** - Comprehensive platform with enterprise features
- **✅ Legal Compliance** - Built-in EU AI Act compliance and legal reference integration
- **✅ Audit & Governance** - Complete traceability and digital signatures
- **✅ AI-Powered** - LLM integration for complex reasoning
- **✅ Open Source** - MIT licensed for maximum adoption

**Ready to transform your business decisions?** [Get started now!](#-get-started-in-5-minutes) 🚀

---

*Built with ❤️ for the future of business decision-making*
