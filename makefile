PYTHON=python3
TESTS=$(wildcard tests/*_test.py)
all: test

.PHONY: test

test:
	$(PYTHON) -m unittest --failfast $(TESTS)
