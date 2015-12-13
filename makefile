PYTHON=python3
#TESTS=$(wildcard tests/*_test.py)
all: test

.PHONY: test clean client server

test:
	$(PYTHON) -m unittest discover --start-directory ./tests -p '*_test.py'
clean:
	rm *.log

