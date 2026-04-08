# CSP Tool Safety Profile - Makefile

.PHONY: test install lint clean help \
        membrane-install membrane-test membrane-test-cov membrane-lint membrane-fmt \
        membrane-schema-check

PYTHON ?= python3
PIP ?= pip
PYTEST ?= pytest
GATEWAY_DIR = reference/python_gateway
MEMBRANE_DIR = reference/python_membrane

help:
	@echo "CSP Tool Safety Profile"
	@echo ""
	@echo "Gateway targets:"
	@echo "  make install              Install reference gateway with dev dependencies"
	@echo "  make test                 Run gateway conformance tests"
	@echo "  make lint                 Run linter (ruff) on gateway"
	@echo "  make clean                Remove build artifacts"
	@echo ""
	@echo "Executor membrane targets (non-normative reference):"
	@echo "  make membrane-install     Install membrane reference verifier"
	@echo "  make membrane-test        Run membrane conformance tests"
	@echo "  make membrane-test-cov    Run membrane tests with coverage"
	@echo "  make membrane-lint        Run linter (ruff) on membrane reference"
	@echo "  make membrane-fmt         Format membrane reference"
	@echo "  make membrane-schema-check  Validate settlement_credential.schema.json parses"
	@echo ""

install:
	cd $(GATEWAY_DIR) && $(PIP) install -e ".[dev]"

test:
	cd $(GATEWAY_DIR) && $(PYTEST) tests/ -v

test-cov:
	cd $(GATEWAY_DIR) && $(PYTEST) tests/ -v --cov=src/assay_gateway --cov-report=term-missing

lint:
	cd $(GATEWAY_DIR) && ruff check src/ tests/

fmt:
	cd $(GATEWAY_DIR) && ruff format src/ tests/

membrane-install:
	cd $(MEMBRANE_DIR) && $(PIP) install -e ".[dev]"

membrane-test:
	cd $(MEMBRANE_DIR) && $(PYTEST) tests/ -v

membrane-test-cov:
	cd $(MEMBRANE_DIR) && $(PYTEST) tests/ -v --cov=src/assay_membrane --cov-report=term-missing

membrane-lint:
	cd $(MEMBRANE_DIR) && ruff check src/ tests/

membrane-fmt:
	cd $(MEMBRANE_DIR) && ruff format src/ tests/

membrane-schema-check:
	$(PYTHON) -c "import json; json.load(open('schemas/settlement_credential.schema.json')); print('schemas/settlement_credential.schema.json: parse ok')"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
