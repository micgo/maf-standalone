# GitHub Configuration

This directory contains GitHub-specific configuration files:

## Workflows

- **coveralls.yml**: Simple workflow for running tests and uploading coverage to Coveralls
- **test-coverage.yml**: Comprehensive test matrix across Python versions with coverage reporting
- **ci.yml**: Full CI pipeline including linting, formatting checks, and tests

## Setting up Coveralls

1. Go to [coveralls.io](https://coveralls.io/) and sign in with GitHub
2. Add the `maf-standalone` repository
3. The GitHub token is automatically handled by GitHub Actions
4. Coverage reports will be uploaded automatically on each push to main

## Required Secrets

No additional secrets are required for basic functionality. The workflows use:
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions
- Optional: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` for integration tests