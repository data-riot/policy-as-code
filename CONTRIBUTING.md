# Contributing to Policy as Code

Thank you for your interest in contributing to Policy as Code! This project aims to advance government operations through agentic AI systems with comprehensive legal compliance and audit capabilities.

## 🎯 **Project Status**

**This is a production-grade foundation with excellent type safety and OSS readiness.**

- ✅ **Architecture**: Excellent foundation with comprehensive features
- ✅ **Type Safety**: 66% mypy error reduction achieved
- ✅ **Code Quality**: Production-grade code with comprehensive testing
- 🚧 **OSS Readiness**: Following [PUBLIC_BACKLOG.md](./PUBLIC_BACKLOG.md) for open-source hygiene

See [PROJECT_STATUS.md](./PROJECT_STATUS.md) for complete project status and [Production Readiness Assessment](docs/production-readiness.md) for details.

## 📋 **Development Priorities**

For detailed development priorities, see **[PUBLIC_BACKLOG.md](./PUBLIC_BACKLOG.md)** which focuses on:
- OSS readiness and CI hygiene
- Security scanning and compliance
- Community guidelines and documentation
- Reproducible builds and provenance

## 🤝 **How to Contribute**

### **Types of Contributions**

We welcome contributions in several areas:

1. **🔧 OSS Readiness (P0 Priority)**
   - Default-deny policy enforcement
   - Schema validation in CI
   - Rego test coverage gates
   - GitHub Actions hardening
   - Security scans and compliance

2. **🏗️ Architecture Enhancement**
   - Domain-first data architecture improvements
   - Multi-agent coordination features
   - Cross-domain integration
   - Scalability improvements

3. **⚖️ Legal & Compliance**
   - EU AI Act compliance enhancements
   - Additional legal framework support
   - Bias detection algorithms
   - Audit trail improvements

4. **📚 Documentation**
   - API documentation completion
   - Tutorial improvements
   - Architecture diagrams
   - Use case examples

5. **🧪 Testing & Quality**
   - Test coverage improvements
   - Performance testing
   - Security testing
   - End-to-end testing

### **Getting Started**

1. **Fork the repository** and clone your fork
2. **Read the [Development Guide](docs/getting-started/development.md)** for setup
3. **Check the [Development Roadmap](DEVELOPMENT_ROADMAP.md)** for current priorities
4. **Review [Production Readiness](docs/production-readiness.md)** for implementation status
5. **Create a new branch** for your contribution

### **Development Setup (macOS)**

```bash
# Clone your fork
git clone https://github.com/your-org/policy-as-code.git
cd policy-as-code

# Create virtual environment (macOS specific)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip3 install -r requirements-dev.txt

# Run tests
python3 -m pytest

# Run linting
python3 -m flake8 policy_as_code tests
python3 -m black --check policy_as_code tests
python3 -m mypy policy_as_code

# Run comprehensive demo
python3 examples/comprehensive_demo.py
```

### **Local-First Development Approach**

**Start simple, add complexity only when needed:**

1. **Single-file solutions** - Begin with `app.py` using Streamlit
2. **Local data files** - Use CSV/JSON before databases
3. **Local development** - Everything runnable on localhost first
4. **Progressive enhancement** - Add complexity only when simple solutions hit limits

**Technology progression:**
- **Frontend**: Streamlit → Vue.js (only for custom UI)
- **Backend**: Single-file Streamlit → FastAPI → Django (only for full business apps)
- **Database**: Local files → DuckDB → SQLite → PostgreSQL

## 📋 **Contribution Guidelines**

### **Language Requirements**

**All contributions must be in English:**
- ✅ **Code comments** - English only
- ✅ **Documentation** - English only
- ✅ **Commit messages** - English only
- ✅ **Pull request descriptions** - English only
- ✅ **Variable names** - English only
- ✅ **Function names** - English only

### **Code Style Guidelines**

**Python Code Standards:**
```python
# Use f-strings for formatting
name = f"user_{user_id}"

# Prefer simple loops over complex comprehensions for data work
results = []
for item in data:
    if item.is_valid():
        results.append(process_item(item))

# Use pathlib for file operations
from pathlib import Path
data_file = Path("data/input.csv")

# Use context managers for files/databases
with open(data_file, 'r') as f:
    content = f.read()

# Use pandas DataFrames as primary data structure
import pandas as pd
df = pd.read_csv("data/file.csv")
```

**Documentation Standards:**
```python
def process_eligibility_request(
    request_data: Dict[str, Any],
    context: DecisionContext
) -> EligibilityResult:
    """
    Process an eligibility request using domain-specific logic.

    Args:
        request_data: Dictionary containing request parameters
        context: Decision context with domain information

    Returns:
        EligibilityResult with decision and reasoning

    Raises:
        ValidationError: If request data is invalid
        DomainError: If domain-specific validation fails
    """
    # Implementation here
    pass
```

### **Commit Messages**

Use clear, descriptive commit messages:

```
feat: add PostgreSQL persistence for decision registry
fix: resolve memory leak in trace ledger
docs: update API documentation with examples
test: add integration tests for domain agents
```

### **Development Workflow**

**Step-by-step contribution process:**

1. **Fork and Clone**
   ```bash
   # Fork the repository on GitHub, then clone your fork
   git clone https://github.com/your-org/policy-as-code.git
   cd policy-as-code
   ```

2. **Setup Development Environment**
   ```bash
   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate

   # Install dependencies
   pip3 install -r requirements-dev.txt

   # Verify setup
   python3 -m pytest tests/test_working.py
   ```

3. **Create Feature Branch**
   ```bash
   # Create branch from main
   git checkout -b feature/your-feature-name

   # Or for bug fixes
   git checkout -b fix/issue-description
   ```

4. **Make Changes**
   - Write code following the style guidelines
   - Add comprehensive tests for new functionality
   - Update documentation as needed
   - Ensure all comments and documentation are in English

5. **Test Your Changes**
   ```bash
   # Run all tests
   python3 -m pytest

   # Run specific test file
   python3 -m pytest tests/test_your_feature.py

   # Run with coverage
   python3 -m pytest --cov=policy_as_code
   ```

6. **Code Quality Checks**
   ```bash
   # Format code
   python3 -m black policy_as_code tests

   # Check code style
   python3 -m flake8 policy_as_code tests

   # Type checking
   python3 -m mypy policy_as_code

   # Security check
   python3 -m bandit -r policy_as_code
   ```

7. **Commit Changes**
   ```bash
   # Stage changes
   git add .

   # Commit with descriptive message
   git commit -m "feat: add eligibility validation for healthcare domain"

   # Push to your fork
   git push origin feature/your-feature-name
   ```

8. **Create Pull Request**
   - Use the provided PR template
   - Include clear description of changes
   - Reference any related issues
   - Ensure all CI checks pass

### **Pull Request Template**

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Security enhancement

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Documentation
- [ ] Documentation updated
- [ ] README updated (if needed)
- [ ] API docs updated (if needed)

## Production Impact
- [ ] No production impact (framework/mock changes)
- [ ] Production hardening (real implementation)
- [ ] Breaking changes (documented)

## Checklist
- [ ] Code follows project standards
- [ ] Tests pass locally
- [ ] Linting passes
- [ ] Documentation updated
- [ ] Ready for review
```

## 🎯 **Current Priorities**

### **Phase 2: Production Hardening (4-6 weeks)**

**High Priority:**
1. **Database Persistence** - Replace in-memory storage with PostgreSQL
2. **LLM Integration** - Replace mocks with real LLM providers
3. **KMS Integration** - Implement AWS/GCP KMS for digital signatures
4. **Production Deployment** - Kubernetes manifests and deployment scripts

**Medium Priority:**
5. **Performance Monitoring** - Prometheus/Grafana integration
6. **Security Hardening** - Encryption at rest and in transit
7. **Bias Detection** - Algorithmic implementation of bias detection
8. **API Completion** - Complete OpenAPI specification

### **Phase 3: Enterprise Features (8-12 weeks)**

**Planned:**
- Multi-tenant support
- Advanced analytics dashboard
- Custom domain creation
- Enterprise integrations
- Compliance automation

## 🏗️ **Architecture Guidelines**

### **Domain-First Data Architecture**

When contributing to the data architecture:

- **Maintain domain boundaries** - Keep healthcare, taxation, immigration separate
- **Preserve semantic context** - Don't dilute domain expertise
- **Implement intent-based discovery** - Only load relevant data
- **Monitor for drift** - Detect changes in domain context

### **Legal Compliance**

All contributions must maintain legal compliance:

- **EU AI Act compliance** - Follow risk classification guidelines
- **Anti-discrimination** - No age, gender, or nationality-based penalties
- **Legal references** - Include proper Finlex/EUR-Lex references
- **Audit trails** - Maintain comprehensive logging

### **Security Standards**

- **No hardcoded secrets** - Use environment variables
- **Input validation** - Sanitize all inputs
- **Rate limiting** - Implement appropriate limits
- **Audit logging** - Log all security-relevant events

### **Testing Requirements**

**Test Coverage Standards:**
- **Unit tests** for all new functions and classes
- **Integration tests** for component interactions
- **Error handling tests** for edge cases and exceptions
- **Performance tests** for critical data processing paths
- **Security tests** for input validation and authentication

**Test Structure Example:**
```python
import pytest
from unittest.mock import Mock, patch
from policy_as_code.core.engine import DecisionEngine

class TestDecisionEngine:
    """Test decision engine functionality"""

    @pytest.fixture
    def engine(self):
        """Setup decision engine for testing"""
        return DecisionEngine()

    @pytest.fixture
    def sample_request(self):
        """Sample request data for testing"""
        return {
            "applicant_id": "test_123",
            "domain": "healthcare",
            "criteria": {"age": 25, "income": 50000}
        }

    @pytest.mark.asyncio
    async def test_process_request_success(self, engine, sample_request):
        """Test successful request processing"""
        result = await engine.process_request(sample_request)
        assert result.status == "approved"
        assert result.reasoning is not None

    def test_invalid_request_data(self, engine):
        """Test handling of invalid request data"""
        with pytest.raises(ValidationError):
            engine.validate_request({})

    @pytest.mark.asyncio
    async def test_domain_error_handling(self, engine):
        """Test domain-specific error handling"""
        invalid_request = {"domain": "invalid_domain"}
        with pytest.raises(DomainError):
            await engine.process_request(invalid_request)
```

## 📚 **Documentation Standards**

### **Code Documentation**

- **Docstrings** for all functions and classes
- **Type hints** for all parameters and return values
- **Examples** in docstrings when appropriate
- **Error documentation** for exception cases

### **API Documentation**

- **OpenAPI specification** updates
- **Example requests/responses**
- **Error code documentation**
- **Authentication requirements**

## 🚫 **What Not to Contribute**

### **Avoid These Changes**

- **Breaking changes** without prior discussion and approval
- **Hardcoded secrets** or sensitive data (use environment variables)
- **Discriminatory logic** or bias based on protected characteristics
- **Non-compliant features** that violate EU AI Act or other regulations
- **Performance regressions** without clear justification and documentation
- **Non-English comments** or documentation (English only policy)
- **Complex microservices** for simple prototypes (start with single-file solutions)
- **Proprietary databases** (Oracle, SQL Server) - use open source alternatives
- **Heavy enterprise frameworks** (Spring, .NET) - prefer lightweight solutions

### **Security Considerations**

- **Never commit secrets** or API keys to version control
- **Validate all inputs** to prevent injection attacks
- **Follow OWASP guidelines** for web security best practices
- **Implement proper authentication** for all new endpoints
- **Use HTTPS** for all external communications
- **Implement rate limiting** to prevent abuse
- **Log security events** for audit and monitoring

## 🎉 **Recognition**

Contributors will be recognized in:

- **CONTRIBUTORS.md** file
- **Release notes** for significant contributions
- **Documentation** for major features
- **GitHub contributors** page

## 📞 **Getting Help**

### **Communication Channels**

- **GitHub Issues** for bug reports and feature requests
- **GitHub Discussions** for questions and ideas
- **Pull Request comments** for code review discussions

### **Resources**

- **[Development Guide](docs/getting-started/development.md)** - Setup and development
- **[Architecture Documentation](docs/architecture/)** - System design
- **[API Reference](docs/reference/api.md)** - API documentation
- **[Compliance Guide](docs/compliance/)** - Legal requirements

## 📄 **License**

By contributing to Policy as Code, you agree that your contributions will be licensed under the MIT License.

## 🙏 **Thank You**

Thank you for contributing to Policy as Code! Your contributions help advance government technology and create more efficient, transparent, and compliant public services.

---

*This contributing guide is part of the Policy as Code project. For questions or suggestions about this guide, please open an issue.*
