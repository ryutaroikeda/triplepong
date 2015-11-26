PYTHON=python3
TESTS=$(wildcard tests/*_test.py)
all: test

.PHONY: test clean

test:
	$(PYTHON) -m unittest --failfast $(TESTS)

clean:
	rm *.log
