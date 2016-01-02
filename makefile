PYTHON=python3
TESTS=$(wildcard tests/*_test.py)

default: test

.PHONY: test clean coverage travis all stress profile

all: coverage travis

test:
	$(PYTHON) -m unittest discover --start-directory ./tests -p \
	       	'*_test.py' 1> unittest.log

profile:
	$(PYTHON) tests/unittestprofile.py

stress:
	for ((i=0;i<10;i++)) do make test; done &> .tmp

clean:
	rm *.log

# Use {code}coverage report{code} to see the result.
coverage:
	coverage run -m unittest discover --start-directory ./tests -p \
		'*_test.py'

# Lint for the travis file.
travis: .travis.yml
	travis lint
