# Contributing to Silicon Archaeology Skill

Thank you for your interest in contributing to the Silicon Archaeology Skill! This project bridges digital archaeology with modern blockchain attestation systems.

## About This Project

Silicon Archaeology Skill is a Python-based tool for:
- Cataloging rare hardware and vintage computing equipment
- Archiving software assets and digital artifacts
- Bridging discoveries to Beacon agent identities
- Creating RustChain Proof-of-Antiquity attestations

## Quick Start

### Prerequisites

- Python 3.9+
- Git
- Basic understanding of digital preservation concepts (helpful but not required)

### Setup

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/silicon-archaeology-skill.git
   cd silicon-archaeology-skill
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install dependencies**:
   ```bash
   pip install -e .
   ```
5. **Copy and configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/add-hardware-catalog`
- `fix/attestation-validation`
- `docs/api-examples`

### 2. Make Your Changes

- Follow existing code style
- Add tests for new functionality
- Update documentation as needed
- Ensure your code handles edge cases

### 3. Test Your Changes

```bash
# Run the test suite
pytest

# Run with coverage
pytest --cov=silicon_archaeology

# Check code style
flake8 silicon_archaeology/
black --check silicon_archaeology/
```

### 4. Commit Your Changes

We follow conventional commits:

```
feat: Add new hardware catalog parser
fix: Resolve attestation timestamp issue
docs: Update API documentation
test: Add tests for beacon bridge
refactor: Simplify proof generation
style: Format code with black
```

### 5. Push and Create a Pull Request

```bash
git push origin feature/your-feature-name
```

Then open a pull request on GitHub with:
- Clear description of changes
- Reference to any related issues
- Testing instructions
- Screenshots/examples if applicable

## Code Style Guidelines

### Python

- Follow PEP 8
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use docstrings for functions and classes

Example:
```python
def catalog_hardware(
    manufacturer: str,
    model: str,
    year: int,
    condition: str
) -> dict:
    """
    Catalog a hardware item in the archive.
    
    Args:
        manufacturer: Hardware manufacturer name
        model: Model identifier
        year: Year of manufacture
        condition: Current condition description
        
    Returns:
        Dictionary containing catalog entry metadata
    """
    # Implementation
```

### Documentation

- Use clear, concise language
- Include code examples
- Update README.md if adding features
- Document API changes

## Areas for Contribution

### High Priority

- Hardware catalog expansion
- Beacon integration improvements
- Proof-of-Antiquity validation
- Documentation and tutorials

### Good First Issues

Look for issues labeled:
- `good first issue`
- `help wanted`
- `documentation`

### Feature Ideas

- Additional hardware database connectors
- Image recognition for hardware identification
- Export formats (CSV, JSON-LD, etc.)
- Web interface improvements

## Reporting Issues

### Bug Reports

Include:
1. Description of the issue
2. Steps to reproduce
3. Expected behavior
4. Actual behavior
5. Environment details (OS, Python version)
6. Relevant logs or error messages

### Feature Requests

Include:
1. Use case description
2. Proposed solution
3. Alternatives considered
4. Additional context

## RTC Bounties

Contributions may be eligible for RTC token rewards:

| Contribution Type | Reward Range |
|------------------|--------------|
| Bug fixes | 2-5 RTC |
| Documentation | 1-3 RTC |
| Small features | 5-10 RTC |
| Major features | 10-25 RTC |
| Code review | 1-2 RTC |

Check [rustchain-bounties](https://github.com/Scottcjn/rustchain-bounties) for active bounty listings.

## Questions?

- Open an issue for questions
- Check existing documentation
- Review closed issues for similar questions

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect maintainers' decisions

---

Thank you for helping preserve computing history! 🏛️💾
