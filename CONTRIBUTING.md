# Contributing to MindFlow

Thanks for your interest in contributing to MindFlow! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Testing](#testing)
- [Reporting Issues](#reporting-issues)
- [License](#license)

## Getting Started

MindFlow is a system-wide AI-powered autocomplete for Linux, built as an IBus input method engine using Python and Google Gemini.

### Prerequisites

- Linux with IBus (Ubuntu, Zorin OS, Fedora, etc.)
- Python 3.10+
- Google Gemini API key ([get one free](https://aistudio.google.com/apikey))
- `python3-gi` and `ibus` development packages

## Development Setup

```bash
# Clone the repository
git clone https://github.com/seemoo/mindflow.git
cd mindflow

# Create virtual environment with system GI bindings
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

### System Dependencies (Ubuntu/Debian)

```bash
sudo apt install -y ibus libibus-1.0-dev gir1.2-ibus-1.0 python3-gi
```

## Project Structure

```
mindflow/
├── mindflow/
│   ├── __init__.py          # Package init
│   ├── constants.py         # App constants
│   ├── config.py            # Configuration management
│   ├── gemini_client.py     # Gemini API wrapper
│   ├── predictor.py         # Prediction caching & debouncing
│   └── engine.py            # IBus engine (core logic)
├── data/
│   ├── mindflow.xml         # IBus component descriptor
│   └── mindflow-engine.xml  # Engine metadata
├── tests/
│   ├── test_config.py       # Config tests
│   ├── test_gemini_client.py # Gemini client tests
│   ├── test_predictor.py    # Predictor tests
│   ├── test_engine_bootstrap.py # Engine unit tests
│   └── integration_test.py  # Manual integration test
├── install.sh               # Installation script
├── uninstall.sh             # Uninstallation script
└── setup.py                 # Package configuration
```

## How to Contribute

### Types of Contributions

- **Bug Reports** — Found a bug? Open an issue with steps to reproduce.
- **Feature Requests** — Have an idea? Open an issue describing the feature.
- **Code Contributions** — Fix a bug or implement a feature via pull request.
- **Documentation** — Improve README, add examples, fix typos.
- **Testing** — Add test coverage, test on different distros.

### Finding Issues

Look for issues labeled:
- `good first issue` — Great for newcomers
- `help wanted` — We need help with these
- `bug` — Confirmed bugs to fix

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** from `master`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the code style guidelines
4. **Add tests** for new functionality
5. **Run the test suite**:
   ```bash
   pytest tests/ -v
   ```
6. **Commit** with clear messages (see [Commit Messages](#commit-messages))
7. **Push** to your fork and open a **Pull Request**
8. **Describe** your changes in the PR description

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation changes
- `test` — Adding or updating tests
- `refactor` — Code refactoring (no feature or fix)
- `chore` — Maintenance tasks
- `perf` — Performance improvements

**Examples:**
```
feat(engine): add arrow key navigation for predictions
fix(gemini): handle None response from safety filters
docs(readme): update installation instructions
test(predictor): add cache invalidation tests
```

## Code Style

- Follow **PEP 8** for Python code
- Use **type hints** for function signatures
- Write **docstrings** for all public classes and methods
- Keep functions **small and focused** (under 30 lines preferred)
- Use **meaningful variable names**

### Formatting

```bash
# Check formatting
ruff check .

# Auto-fix
ruff check --fix .
```

## Testing

### Running Tests

```bash
# All unit tests
pytest tests/ -v

# Specific test file
pytest tests/test_engine.py -v

# With coverage
pytest tests/ --cov=mindflow --cov-report=html
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_<module>.py`
- Name test functions `test_<what_it_tests>`
- Use `pytest` fixtures for shared setup
- Mock external dependencies (Gemini API, IBus)

### Test Categories

| File | What it tests |
|------|---------------|
| `test_config.py` | Config loading, saving, defaults |
| `test_gemini_client.py` | API client, response parsing |
| `test_predictor.py` | Caching, debouncing |
| `test_engine_bootstrap.py` | Engine keystroke handling, predictions |
| `integration_test.py` | Full pipeline with real API (manual) |

## Reporting Issues

When reporting bugs, please include:

1. **OS and version** (e.g., Ubuntu 24.04, Zorin OS 18.1)
2. **IBus version** (`ibus version`)
3. **Python version** (`python3 --version`)
4. **Steps to reproduce**
5. **Expected behavior**
6. **Actual behavior**
7. **Logs** (if applicable):
   ```bash
   # Enable debug logging
   export MINDFLOW_LOG_LEVEL=DEBUG
   ibus engine mindflow
   ```

## Feature Requests

When suggesting features:

1. **Describe the problem** you're trying to solve
2. **Describe the solution** you'd like
3. **Consider alternatives** you've thought about
4. **Additional context** (screenshots, examples)

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

## Questions?

Open an issue with the `question` label, or start a discussion in the repository.

---

Thank you for contributing to MindFlow! 🪄
