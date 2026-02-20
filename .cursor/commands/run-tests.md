# Run Tests

Run the test suite with coverage reporting.

```bash
uv run pytest tests/ --cov=src --cov-report=html
```

This command:
- Runs all tests in the `tests/` directory
- Generates coverage report for `src/` module
- Creates HTML coverage report in `htmlcov/`
