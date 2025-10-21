# Contributing to Decision Layer

Thank you for your interest in contributing to Decision Layer! This document provides guidelines and information for contributors.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a virtual environment: `python -m venv .venv`
4. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
5. Install dependencies: `pip install -e .[dev]`

## Development Setup

### Prerequisites
- Python 3.10 or higher
- pip

### Running Tests
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=decision_layer

# Run specific test file
pytest tests/test_executor.py
```

### Code Quality
```bash
# Format code
black decision_layer tests

# Check code style
flake8 decision_layer tests

# Type checking (if mypy is configured)
mypy decision_layer
```

## Making Changes

1. Create a new branch for your feature/fix
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation if needed
6. Commit your changes with clear commit messages

### Commit Message Format
Use conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Examples:
- `feat(executor): add support for conditional policies`
- `fix(cli): resolve argument parsing issue`
- `docs(readme): update installation instructions`

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update any relevant documentation
3. Ensure your code follows the project's style guidelines
4. Add tests for any new functionality
5. Ensure all tests pass
6. Request review from maintainers

## Code Style Guidelines

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings for public functions and classes
- Keep functions focused and reasonably sized
- Use type hints where appropriate

## Testing Guidelines

- Write tests for all new functionality
- Ensure existing tests continue to pass
- Use descriptive test names
- Group related tests in test classes
- Use fixtures for common test data

## Reporting Issues

When reporting issues, please include:

- A clear description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Any relevant error messages or logs

## Questions or Need Help?

If you have questions or need help, please:

1. Check existing issues and discussions
2. Create a new issue with the "question" label
3. Reach out to maintainers

Thank you for contributing to Decision Layer!
