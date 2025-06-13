# Contributing to Multi-Agent Framework

Thank you for your interest in contributing to the Multi-Agent Framework! We welcome contributions from the community and are excited to collaborate with you.

## Code of Conduct

By participating in this project, you agree to be respectful and constructive in all interactions. We expect all contributors to:

- Be welcoming and inclusive
- Respect differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what's best for the community

## How to Contribute

### Reporting Issues

1. Check if the issue already exists in the [issue tracker](https://github.com/micgo/maf-standalone/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce (if applicable)
   - Expected vs actual behavior
   - System information (Python version, OS, etc.)
   - Error messages or logs

### Suggesting Features

1. Check existing issues and discussions for similar ideas
2. Open a new issue with the "feature request" label
3. Describe the feature and its use case
4. Explain why it would benefit the project

### Contributing Code

#### Setup Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/maf-standalone.git
   cd maf-standalone
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

#### Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Write or update tests
4. Run tests:
   ```bash
   python test_framework.py
   pytest tests/
   ```
5. Format your code:
   ```bash
   black --line-length 100 .
   ```
6. Check types (if applicable):
   ```bash
   mypy multi_agent_framework/
   ```
7. Commit with clear messages:
   ```bash
   git commit -m "feat: add new feature X"
   ```

#### Pull Request Process

1. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Create a Pull Request on GitHub
3. Fill out the PR template completely
4. Ensure all CI checks pass
5. Wait for review and address feedback

### Commit Message Convention

We follow conventional commits format:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Test additions or changes
- `chore:` Maintenance tasks

Examples:
```
feat: add support for custom agent configurations
fix: resolve task assignment deadlock issue
docs: update README with new CLI commands
```

## Development Guidelines

### Code Style

- Follow PEP 8 with 100-character line limit
- Use type hints where appropriate
- Write descriptive variable and function names
- Add docstrings to all public functions and classes

### Testing

- Write tests for new features
- Maintain or improve code coverage
- Test edge cases and error conditions
- Use descriptive test names

### Documentation

- Update README.md for user-facing changes
- Add inline comments for complex logic
- Update API documentation if applicable
- Include examples in docstrings

## Architecture Decisions

When proposing significant changes:

1. Open an issue for discussion first
2. Consider backward compatibility
3. Think about performance implications
4. Ensure changes align with project goals

## Getting Help

- Check the [documentation](https://github.com/micgo/maf-standalone/wiki)
- Ask questions in [GitHub Discussions](https://github.com/micgo/maf-standalone/discussions)
- Join our community chat (if available)

## Recognition

Contributors will be recognized in:
- The project's contributors list
- Release notes for significant contributions
- Special mentions for exceptional contributions

Thank you for helping make the Multi-Agent Framework better!