first: all

all:

test:
	python3 -m unittest discover -v tests/ '*_test.py'

