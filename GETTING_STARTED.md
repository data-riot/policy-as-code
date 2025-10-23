# 🚀 Getting Started Guide

> **Everything you need to get up and running with Policy as Code Foundation**

## 🎯 **Quick Start (2 minutes)**

```bash
# Clone and install (minimal dependencies)
git clone https://github.com/your-org/policy-as-code.git
cd policy-as-code
pip3 install -e .

# Initialize and run your first decision
policy-as-code init
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

## 📊 **What Works Right Now**

### ✅ **Core Features (Working)**
- **CLI Interface** - Deploy, execute, and manage decision functions
- **Basic Decision Functions** - Simple business logic with validation
- **Working Examples** - Loan approval, basic approval, multi-criteria decisions
- **Progressive Learning** - Step-by-step examples that actually work
- **Extensible Architecture** - Ready for advanced features

### 🚧 **In Development**
- **Legal Compliance Framework** - Finlex/EUR-Lex integration
- **Digital Signatures** - Change control and separation of duties
- **Immutable Trace Ledger** - Hash-chained audit trail
- **Agentic AI Integration** - LLM-powered reasoning

### 🔮 **Future Vision**
- **EU AI Act Compliance** - High-risk system compliance
- **Cross-Border Architecture** - EU AI Commons implementation
- **Citizen Explanation API** - Human-readable decision justifications
- **Advanced Governance** - Drift detection and independent audit

---

## 🎓 **Progressive Learning Path**

### **Level 1: Basic Decisions** (5 minutes)

**Start here**: `python3 examples/simple_demo.py`

**What you'll learn**:
- Simple decision structure
- Input/output validation
- Basic business rules
- Error handling

**Example**:
```python
def simple_loan_approval(input_data):
    credit_score = input_data.get("credit_score", 0)
    income = input_data.get("income", 0)

    if credit_score >= 700 and income >= 50000:
        return {"approved": True, "amount": min(income * 3, 500000)}
    else:
        return {"approved": False, "reason": "Criteria not met"}
```

### **Level 2: CLI Usage** (10 minutes)

**Try this**: Use the CLI to deploy and execute functions

**What you'll learn**:
- Function deployment
- Execution with real data
- Registry management
- CLI commands

**Commands**:
```bash
# Initialize the system
policy-as-code init

# Deploy a function
policy-as-code deploy loan_approval 1.0 examples/simple_demo.py

# Execute with data
policy-as-code execute loan_approval '{"credit_score": 750, "income": 75000}'

# List deployed functions
policy-as-code list

# Get function info
policy-as-code info loan_approval
```

### **Level 3: Multi-Criteria Decisions** (15 minutes)

**Try this**: `python3 examples/level1_basic_approval.py`

**What you'll learn**:
- Age and income validation
- Multiple criteria checking
- Clear error messages
- Structured output format

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

### **Level 4: OPA Integration** (60 minutes)

**Try this**: `python3 examples/opa_demo.py`

**What you'll learn**:
- OPA/Rego policy integration
- Python-OPA bridge (shows current gap)
- Policy-as-code with Rego
- Integration challenges and solutions

**Note**: This demo shows the integration gap between Python examples and OPA/Rego policies that needs to be fixed.

### **Level 5: Build Your Own** (90 minutes)

**Explore**: Create your own decision function

**What you'll learn**:
- Writing decision functions
- Deploying with CLI
- Testing with real data
- Understanding the architecture

---

## 🏗️ **Architecture Overview**

### **System Components**

```
┌─────────────────────────────────────────────────────────────┐
│                    Policy as Code Platform                  │
├─────────────────────────────────────────────────────────────┤
│ • CLI Interface      • Decision Engine                      │
│ • Function Registry  • Basic Validation                     │
│ • Working Examples   • Extensible Framework                 │
└─────────────────────────────────────────────────────────────┘
```

### **Decision Flow**

```
Input Data → Validation → Decision Function → Output Validation → Registry
     ↓            ↓              ↓                ↓              ↓
  JSON/YAML   Basic        Your Business    Basic        Function
  Schema      Validation   Logic Code       Validation   Registry
     ↓            ↓              ↓                ↓              ↓
  Type Safe   Error Handling  Deterministic   Consistent    Version
  Input       & Reporting    Execution       Output        Control
```

### **Key Features**

- **🔒 Function Registry** - Versioned storage of decision functions
- **📜 CLI Interface** - Easy deployment and execution
- **🧠 Decision Engine** - Basic function execution and validation
- **📊 Audit Trail** - Every decision is logged
- **🔌 Extensible** - Ready for advanced features

---

## 🆘 **Troubleshooting**

### **Common Issues**

#### **"command not found: policy-as-code"**

**Solution**:
```bash
# Reinstall the package
pip3 install -e .

# Check if CLI is installed
which policy-as-code

# If not found, add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

#### **"ModuleNotFoundError: No module named 'policy_as_code'"**

**Solution**:
```bash
# Install in development mode
pip3 install -e .

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### **"Permission denied" errors**

**Solution**:
```bash
# Use user install
pip3 install --user -e .

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip3 install -e .
```

#### **"Function not found in registry"**

**Solution**:
```bash
# Initialize the system first
policy-as-code init

# Deploy a function
policy-as-code deploy my_function 1.0 my_function.py

# List available functions
policy-as-code list
```

### **Quick Diagnosis**

```bash
# Check if Python is working
python3 --version

# Check if package is installed
python3 -c "import policy_as_code; print('✅ Package installed')"

# Check if CLI is working
policy-as-code --help

# Check if examples work
python3 examples/simple_demo.py

# Check system status
policy-as-code status
```

### **Debug Mode**

```bash
# Enable debug logging
export DEBUG=1

# Run CLI with debug
policy-as-code --debug execute loan_approval '{"credit_score": 750}'
```

---

## 🎯 **Next Steps**

### **After Level 1**
1. **Modify the examples** - Change the business logic
2. **Add more criteria** - Employment status, down payment, etc.
3. **Try Level 2** - Use the CLI interface

### **After Level 2**
1. **Deploy your own function** - Create a new decision function
2. **Test with real data** - Use the CLI to execute with your data
3. **Try Level 3** - Multi-criteria decisions

### **After Level 3**
1. **Build something real** - Your own decision function
2. **Use the CLI** - Deploy and execute your function
3. **Explore architecture** - Understand how it all works

### **After Level 4**
1. **Contribute** - Help improve the project
2. **Share** - Show others what you built
3. **Scale** - Build enterprise systems

---

## 🚀 **Ready to Start?**

**Choose your path**:

- **Quick Explorer** (2 min): Run `python3 examples/simple_demo.py`
- **CLI User** (10 min): Use `policy-as-code` commands
- **Learner** (1 hour): Follow the progressive levels
- **Builder** (30 min): Create your own function

**Need help?** Check the troubleshooting section above or open a GitHub issue.

---

*Happy coding! 🚀*
