# Install dependencies
depend:
	pip install -e .

# Run tests.
check:
	py.test --pep8
	python setup.py test
