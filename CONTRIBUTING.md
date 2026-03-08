# Contributing to Velvet Interface

Thank you for your interest in contributing to Velvet Interface!

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you agree to uphold this standard. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

- Check if the issue already exists in [GitHub Issues](https://github.com/velvet-ai/velvet-interface/issues)
- Provide clear steps to reproduce
- Include Python version, OS, and relevant error messages
- Specify which surface (Qt, web, etc.) you're using

### Suggesting Features

- Open a discussion in [GitHub Discussions](https://github.com/velvet-ai/velvet-interface/discussions)
- Describe the use case and expected behavior
- Consider backward compatibility
- Note which surfaces the feature would apply to

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run tests: `pytest tests/`
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request against `main`

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git

### Setup

```bash
git clone https://github.com/YOUR_USERNAME/velvet-interface.git
cd velvet-interface
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .[dev,qt]
```

### Running Tests

```bash
pytest tests/
```

### Type Checking

```bash
mypy velvet_interface/
```

### Code Style

```bash
black velvet_interface/
```

## Project Structure

```
velvet-interface/
├── velvet_interface/
│   ├── core/           # Framework primitives
│   ├── surfaces/       # Surface implementations
│   ├── scenes/         # Example scenes
│   └── utils/          # Utilities
├── docs/               # Documentation
├── examples/           # Example applications
└── tests/              # Test suite
```

## Guidelines

### Scene Development

- Scenes must be surface-agnostic
- Use Surface API for rendering
- Implement on_enter/on_exit lifecycle
- Add type hints
- Include docstrings

### Surface Development

- Implement all abstract methods from Surface base class
- Handle errors gracefully
- Provide fallbacks for missing features
- Document surface-specific behavior

### Code Style

- Follow PEP 8
- Use type hints where possible
- Add docstrings to public APIs
- Keep functions focused and small

## Commit Guidelines

### Format

```
type(scope): brief description

Longer explanation if needed.

Fixes #123
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions or fixes
- `refactor`: Code refactoring (no functional change)
- `chore`: Build/tooling changes

### Examples

```
feat(qt): add drag-and-drop support

Implement drag-and-drop for Qt surface using QDrag.

Fixes #42
```

```
fix(router): prevent duplicate scene registration

Scenes with same ID now raise ValueError instead of
silently replacing.

Fixes #67
```

## Review Process

1. Maintainers review PRs within 7 days
2. At least one approval required
3. CI tests must pass
4. No merge conflicts

## Surface Development Guide

### Creating a Custom Surface

1. Subclass `Surface` from `velvet_interface.core.surface`
2. Implement all abstract methods
3. Add to `velvet_interface/surfaces/`
4. Create tests in `tests/`
5. Document in `docs/surfaces/`

### Testing Surfaces

- Use pytest for unit tests
- Test all Surface API methods
- Verify scene rendering
- Check error handling

## License

By contributing, you agree that your contributions will be licensed under the GPLv3 License.

## Questions?

- Open a [Discussion](https://github.com/velvet-ai/velvet-interface/discussions)
- Check existing [Issues](https://github.com/velvet-ai/velvet-interface/issues)

Thank you for contributing!
