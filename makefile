PYTHON=python3
TESTS=$(wildcard tests/*_test.py)

default: test

.PHONY: test clean client server coverage travis all default

all: coverage travis

test:
	$(PYTHON) -m unittest discover --start-directory ./tests -p '*_test.py'
clean:
	rm *.log

# Use {code}coverage report{code} to see the result.
coverage:
	coverage run -m unittest discover --start-directory ./tests -p \
		'*_test.py'

# Lint for the travis file.
travis: .travis.yml
	travis lint
