.PHONY: install test lint clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/

lint:
	flake8 src/
	black src/ tests/
	isort src/ tests/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info 