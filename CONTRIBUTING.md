# Contributing to Multi-Agent Framework

Thank you for your interest in contributing to MAF! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/micgo/maf-standalone/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version, MAF version)
   - Error logs

### Suggesting Features

1. Check [Discussions](https://github.com/micgo/maf-standalone/discussions) for similar ideas
2. Create a new discussion or issue with:
   - Clear description of the feature
   - Use cases and benefits
   - Potential implementation approach

### Code Contributions

1. **Fork the Repository**
   ```bash
   git clone https://github.com/your-username/maf-standalone.git
   cd maf-standalone
   ```

2. **Set Up Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make Your Changes**
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

5. **Run Tests**
   ```bash
   python -m pytest tests/
   python -m pytest --cov=multi_agent_framework tests/  # With coverage
   ```

6. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: Add your feature description"
   ```

   Follow conventional commit format:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `test:` Test additions/changes
   - `refactor:` Code refactoring
   - `chore:` Maintenance tasks

7. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a PR on GitHub.

## Development Guidelines

### Code Style

- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and small

### Testing

- Write tests for new features
- Maintain or improve code coverage
- Test edge cases and error conditions

### Documentation

- Update README.md if needed
- Add/update wiki pages for new features
- Include examples in docstrings

## Areas for Contribution

### Good First Issues

Look for issues labeled `good first issue` - these are great for newcomers!

### Priority Areas

1. **Testing**: Increase code coverage (currently 18%)
2. **Documentation**: Improve guides and examples
3. **Agent Development**: Enhance existing agents or create new ones
4. **CLI Features**: Add new commands and options
5. **Integration**: Support for more frameworks

### Roadmap Items

Check [ROADMAP.md](ROADMAP.md) for planned features and improvements.

## Questions?

- Ask in [Discussions](https://github.com/micgo/maf-standalone/discussions)
- Reach out in issues
- Check the [Wiki](https://github.com/micgo/maf-standalone/wiki)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.