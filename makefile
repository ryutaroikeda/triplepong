PYTHON=python3
TESTS=$(wildcard tests/*_test.py)

default: test

.PHONY: test clean coverage travis all stress

all: coverage travis

test:
	$(PYTHON) -m unittest discover --start-directory ./tests -p '*_test.py'

stress:
	for ((i=0;i<100;i++)) do make test; done &> .tmp

clean:
	rm *.log

# Use {code}coverage report{code} to see the result.
coverage:
	coverage run -m unittest discover --start-directory ./tests -p \
		'*_test.py'

# Lint for the travis file.
travis: .travis.yml
	travis lint
