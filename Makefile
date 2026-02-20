.PHONY: help test sync clean run

help:
	@echo "Available commands:"
	@echo "  make test    - Run tests"
	@echo "  make sync    - Sync dependencies"
	@echo "  make run     - Run the SQS listener"
	@echo "  make clean   - Clean test artifacts"

test:
	@echo "Running harness tests..."
	uv run pytest tests/ -v

sync:
	@echo "Syncing harness dependencies..."
	uv sync

run:
	@echo "Starting harness SQS listener..."
	uv run python -m src.main

clean:
	@echo "Cleaning test artifacts..."
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.db" -delete 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -r {} + 2>/dev/null || true
	@echo "Clean complete!"
