# Makefile for vpk module

define HELPBODY
Available commands:

	make help       - this thing.
	make init       - install python dependancies
	make test       - run tests and coverage
	make pylint     - code analysis
	make build      - pylint + test

endef

export HELPBODY
help:
	@echo "$$HELPBODY"

init:
	pip install nose

test:
	rm -f .coverage vpk/*.pyc tests/*.pyc
	PYTHONHASHSEED=0 nosetests --verbosity 2 --with-coverage --cover-package=vpk

pylint:
	pylint -r n -f colorized vpk || true

build: pylint test

clean:
	rm -rf dist vpk.egg-info vpk/*.pyc

dist: clean
	python setup.py sdist

upload: dist
	python setup.py register -r pypi
	twine upload -r pypi dist/*
