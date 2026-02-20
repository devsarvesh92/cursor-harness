# Cursor Agents Configuration

This project uses Cursor as a **harness** - a structured, guided development environment rather than an ad-hoc copilot.

## Available Agents

### Code Reviewer
- Reviews pull requests
- Checks for code quality issues
- Validates against project standards

### Test Generator
- Generates test cases for new features
- Ensures test coverage
- Follows testing best practices

### Documentation Writer
- Generates API documentation
- Updates README files
- Creates inline code documentation

## Workflow

1. **Planning**: Define requirements and acceptance criteria
2. **Development**: Follow project rules and standards
3. **Testing**: Run tests and ensure coverage
4. **Review**: Use agents to review code quality
5. **Documentation**: Update docs with changes

## Rules

All development follows the rules defined in `.cursor/rules/`:
- Python standards
- Project structure conventions
- Testing requirements

## Commands

Use commands in `.cursor/commands/` for common tasks:
- `run-tests` - Execute test suite
- `format-code` - Format and lint code

## Skills

Leverage skills in `.cursor/skills/` for domain-specific knowledge:
- API development patterns
- Database operations
- Authentication flows
