# 🚀 Getting Started Guide

> **Everything you need to get up and running with Policy as Code**

## 🎯 **Quick Start (5 minutes)**

```bash
# Clone and install
git clone https://github.com/your-org/policy-as-code.git
cd policy-as-code
pip3 install -r requirements.txt
pip3 install -e .

# Run your first decision
python3 examples/simple_demo.py
```

**Expected Output:**
```
🚀 Policy as Code - Simple Demo
✅ APPROVED - Amount: $225,000, Interest Rate: 7.0%
❌ DENIED - Credit score below 700; Income below $50,000
✅ APPROVED - Amount: $300,000, Interest Rate: 5.0%
🎉 Demo completed!
```

---

## 🎓 **Progressive Learning**

### **Level 1: Basic Decisions** (15 minutes)

**Start here**: `python3 examples/level1_basic_approval.py`

**What you'll learn**:
- Simple decision structure
- Input/output validation
- Basic business rules
- Error handling

**Example**:
```python
def basic_approval(input_data):
    age = input_data.get("age", 0)
    income = input_data.get("income", 0)

    if age >= 18 and income >= 30000:
        return {"approved": True, "reason": "Meets requirements"}
    else:
        return {"approved": False, "reason": "Does not meet requirements"}
```

### **Level 2: Multi-Criteria Decisions** (30 minutes)

**Try this**: `python3 examples/level1_loan_approval.py`

**What you'll learn**:
- Multiple decision criteria
- Complex business logic
- Risk assessment
- Detailed output format

**Example**:
```python
def loan_approval(input_data):
    credit_score = input_data.get("credit_score", 0)
    income = input_data.get("income", 0)
    debt_ratio = input_data.get("debt_ratio", 0)

    # Multiple criteria checks
    if credit_score < 600:
        return {"approved": False, "reason": "Credit score too low"}

    if income < 40000:
        return {"approved": False, "reason": "Income too low"}

    if debt_ratio > 0.4:
        return {"approved": False, "reason": "Debt ratio too high"}

    # Calculate approval
    max_amount = min(income * 4, 500000)
    interest_rate = 0.05 if credit_score > 750 else 0.07

    return {
        "approved": True,
        "approved_amount": max_amount,
        "interest_rate": interest_rate
    }
```

### **Level 3: Real Applications** (45 minutes)

**Explore**: `examples/demos/` directory

**What you'll learn**:
- Domain-specific logic (healthcare, tax, immigration)
- Legal compliance integration
- Complex workflows
- Production patterns

### **Level 4: Production Systems** (60 minutes)

**Build**: Use the API for real applications

**What you'll learn**:
- API integration (REST, GraphQL, WebSocket)
- Production deployment
- Monitoring and observability
- Scaling strategies

---

## 🏗️ **Architecture Overview**

### **System Components**

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

### **Decision Flow**

```
Input Data → Validation → Decision Function → Output Validation → Audit Trail
     ↓            ↓              ↓                ↓              ↓
  JSON/YAML   Pydantic      Your Business    Pydantic      Immutable
  Schema      Models        Logic Code       Models        Trace Ledger
     ↓            ↓              ↓                ↓              ↓
  Type Safe   Error Handling  Deterministic   Consistent    Cryptographic
  Input       & Reporting    Execution       Output        Hash Chaining
```

### **Key Features**

- **🔒 Immutable Audit Trail** - Every decision is cryptographically signed
- **📜 Legal Compliance** - Built-in legal references (Finlex, EUR-Lex)
- **🧠 AI-Powered Reasoning** - LLM integration for complex decisions
- **📊 Performance Monitoring** - Real-time metrics and alerting
- **🔌 Multiple APIs** - REST, GraphQL, WebSocket, Python SDK

---

## 🆘 **Troubleshooting**

### **Common Issues**

#### **"ModuleNotFoundError: No module named 'policy_as_code'"**

**Solution**:
```bash
# Install in development mode
pip3 install -e .

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### **"ImportError: cannot import name 'FastAPI'"**

**Solution**:
```bash
# Install FastAPI
pip3 install fastapi uvicorn

# Or install all requirements
pip3 install -r requirements.txt
```

#### **"Permission denied" errors**

**Solution**:
```bash
# Use user install
pip3 install --user -r requirements.txt

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

#### **"Port already in use"**

**Solution**:
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
python3 run_api.py --port 8001
```

### **Quick Diagnosis**

```bash
# Check if Python is working
python3 --version

# Check if package is installed
python3 -c "import policy_as_code; print('✅ Package installed')"

# Check if examples work
python3 examples/simple_demo.py
```

### **Debug Mode**

```bash
# Enable debug logging
export DEBUG=1

# Run with verbose output
python3 examples/simple_demo.py --verbose
```

---

## 🎯 **Next Steps**

### **After Level 1**
1. **Modify the examples** - Change the business logic
2. **Add more criteria** - Employment status, down payment, etc.
3. **Try Level 2** - Multi-criteria decisions

### **After Level 2**
1. **Explore real examples** - Healthcare, tax, immigration
2. **Understand the API** - REST, GraphQL, WebSocket
3. **Try Level 3** - Real applications

### **After Level 3**
1. **Build something real** - Your own decision function
2. **Use the API** - Integrate with your application
3. **Deploy to production** - Scalable systems

### **After Level 4**
1. **Contribute** - Help improve the project
2. **Share** - Show others what you built
3. **Scale** - Build enterprise systems

---

## 🚀 **Ready to Start?**

**Choose your path**:

- **Quick Explorer** (5 min): Run `python3 examples/simple_demo.py`
- **Learner** (2 hours): Follow the progressive levels
- **Builder** (1 hour): Jump to API integration
- **Architect** (30 min): Read the architecture overview

**Need help?** Check the troubleshooting section above or open a GitHub issue.

---

*Happy coding! 🚀*
