# Pull Request Summary Feature

The Policy as Code repository includes an automatic pull request summary feature that generates comprehensive summaries of changes for every pull request. This feature helps maintainers and reviewers quickly understand the scope and impact of changes.

## Overview

The PR summary feature automatically:
- Analyzes changed files and categorizes them by Policy as Code components
- Assesses the impact of changes on governance, security, and functionality
- Provides testing recommendations based on the types of changes
- Generates comprehensive summaries with commit messages and change statistics
- Posts summaries as comments on pull requests

## How It Works

### GitHub Actions Workflow

The feature is implemented as a GitHub Actions workflow (`.github/workflows/pr-summary.yml`) that:

1. **Triggers** on pull request events (opened, synchronize, reopened)
2. **Analyzes** changes using git diff and commit analysis
3. **Generates** comprehensive summaries using Python scripts
4. **Posts** summaries as comments on the pull request

### Components

#### 1. Workflow File
- **Location**: `.github/workflows/pr-summary.yml`
- **Triggers**: Pull request events
- **Actions**: Checkout, Python setup, summary generation, comment posting

#### 2. Summary Generator
- **Location**: `scripts/generate_pr_summary.py`
- **Purpose**: Analyzes changes and generates markdown summaries
- **Features**: File categorization, impact assessment, testing recommendations

#### 3. Comment Poster
- **Location**: `scripts/comment_pr_summary.py`
- **Purpose**: Posts generated summaries as PR comments
- **Integration**: Uses GitHub API with GITHUB_TOKEN

#### 4. Configuration
- **Location**: `scripts/pr_summary_config.yaml`
- **Purpose**: Configurable rules, patterns, and templates
- **Customization**: Categories, thresholds, recommendations

## Configuration

### File Categories

The system categorizes files based on Policy as Code patterns:

```yaml
categories:
  decision_functions:
    patterns:
      - "decision_layer/.*\\.py$"
      - "examples/.*\\.py$"
    description: "Decision Functions & Logic"
    icon: "⚖️"
    priority: 1

  governance:
    patterns:
      - "decision_layer/(trace_ledger|legal_refs|release|audit_service)\\.py$"
    description: "Governance & Compliance"
    icon: "🔒"
    priority: 2

  agentic_ai:
    patterns:
      - "decision_layer/(llm_integration|conversational_interface|workflow_orchestration|agent_performance_monitor)\\.py$"
    description: "Agentic AI Features"
    icon: "🤖"
    priority: 3
```

### Impact Assessment

The system assesses impact based on:

- **High-priority categories**: Governance, security, agentic AI, API changes
- **Change size**: Lines added/removed thresholds
- **Complexity**: Files with substantial modifications

### Testing Recommendations

Category-specific testing recommendations:

```yaml
testing_recommendations:
  decision_functions:
    - "Ensure 100% branch coverage for new/modified decision functions"
    - "Verify deterministic execution and time semantics"
    - "Test legal reference validation"

  governance:
    - "Verify trace ledger integrity"
    - "Test legal reference validation"
    - "Validate digital signature workflows"
```

## Summary Sections

Each PR summary includes:

### 1. Change Overview
- Files modified count
- Lines added/removed statistics
- New files count

### 2. Changes by Category
- Files grouped by Policy as Code components
- Prioritized by impact (governance, security, etc.)
- Icons and descriptions for each category

### 3. Impact Assessment
- High-impact change detection
- Large change warnings
- Complex change alerts

### 4. Commit Messages
- Recent commit history
- Limited to configurable number (default: 10)

### 5. Testing Recommendations
- Category-specific testing guidance
- Policy as Code compliance requirements
- SLO and coverage requirements

### 6. Complex Changes
- Files with substantial modifications
- Line change statistics
- Risk assessment

### 7. Policy as Code Considerations
- Governance compliance notes
- Security considerations
- Testing requirements
- Documentation updates

## Example Summary

```markdown
# 📋 Pull Request Summary #123

**Branch**: `feature/new-decision-function` → `main`
**Generated**: 2024-01-15 14:30:00 UTC

## 📊 Change Overview

- **Files Modified**: 5
- **Lines Added**: 234
- **Lines Removed**: 12
- **New Files**: 2

## 📁 Changes by Category

### ⚖️ Decision Functions & Logic
- `decision_layer/core.py`
- `examples/new_policy.py`

### 🔒 Governance & Compliance
- `decision_layer/trace_ledger.py`

## 🎯 Impact Assessment

🔒 **Governance Impact**: Changes to governance & compliance
✅ **Low Impact**: Minor changes with minimal risk

## 🧪 Testing Recommendations

- **Decision Functions**: Ensure 100% branch coverage for new/modified decision functions
- **Governance**: Verify trace ledger integrity

## 🔍 Policy as Code Considerations

- **Governance**: Ensure all decision functions maintain legal compliance and audit trails
- **Testing**: Maintain 100% branch coverage and SLO requirements
```

## Customization

### Adding New Categories

To add new file categories, update `scripts/pr_summary_config.yaml`:

```yaml
categories:
  new_category:
    patterns:
      - "path/to/files/.*\\.ext$"
    description: "New Category Description"
    icon: "🆕"
    priority: 10
```

### Modifying Thresholds

Adjust impact assessment thresholds:

```yaml
impact_thresholds:
  large_change_lines: 1000  # Increase threshold
  complex_change_lines: 200  # Increase threshold
  high_priority_categories:
    - "governance"
    - "security"
    - "new_category"  # Add new high-priority category
```

### Custom Testing Recommendations

Add category-specific testing guidance:

```yaml
testing_recommendations:
  new_category:
    - "Run specific tests for new category"
    - "Verify new category compliance"
```

## Manual Usage

### Generate Summary Locally

```bash
python scripts/generate_pr_summary.py \
  --pr-number 123 \
  --repo-owner your-org \
  --repo-name policy-as-code \
  --base-branch main \
  --head-branch feature-branch \
  --config-file scripts/pr_summary_config.yaml \
  --output pr_summary.md
```

### Post Summary Comment

```bash
export GITHUB_TOKEN="your-token"
python scripts/comment_pr_summary.py \
  --pr-number 123 \
  --repo-owner your-org \
  --repo-name policy-as-code \
  --summary-file pr_summary.md
```

## Troubleshooting

### Common Issues

1. **Missing GITHUB_TOKEN**: Ensure the token is set in repository secrets
2. **Config file not found**: The script falls back to default configuration
3. **Git diff errors**: Ensure the repository has proper git history
4. **API rate limits**: GitHub API has rate limits for comments

### Debug Mode

Enable debug output by modifying the workflow:

```yaml
- name: Generate PR Summary
  env:
    DEBUG: "true"
  run: |
    python scripts/generate_pr_summary.py --debug
```

## Integration with Policy as Code

The PR summary feature is specifically designed for Policy as Code repositories and includes:

- **Governance awareness**: Recognizes governance-critical changes
- **Security focus**: Highlights security-related modifications
- **Compliance tracking**: Ensures legal and audit requirements
- **Testing rigor**: Enforces SLO and coverage requirements
- **Documentation**: Maintains comprehensive change documentation

## Future Enhancements

Potential improvements:

1. **AI-powered analysis**: Use LLM integration for deeper change analysis
2. **Risk scoring**: Automated risk assessment based on change patterns
3. **Compliance checking**: Integration with legal reference validation
4. **Performance impact**: Analysis of performance implications
5. **Dependency analysis**: Impact on dependent systems and APIs

## Contributing

To contribute to the PR summary feature:

1. **Update configuration**: Modify `scripts/pr_summary_config.yaml`
2. **Enhance analysis**: Improve `scripts/generate_pr_summary.py`
3. **Add integrations**: Extend `scripts/comment_pr_summary.py`
4. **Improve documentation**: Update this documentation file

The feature is designed to be extensible and configurable for different Policy as Code implementations.
