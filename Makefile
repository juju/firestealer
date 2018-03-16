DEVENV=devenv
SYSDEPS=build-essential python3-virtualenv tox

.PHONY: all
all: help

$(DEVENV):
	tox -e $(DEVENV)

dev: $(DEVENV)

.PHONY: dist
dist: clean dev check
	$(DEVENV)/bin/python setup.py sdist bdist_wheel

.PHONY: check
check:
	tox

.PHONY: clean
clean:
	rm -rf $(DEVENV) .tox dist *.egg-info

.PHONY: help
help:
	@echo make dev - create the development environment
	@echo make test - run unit tests
	@echo make check - run lint and tests on the resulting packages
	@echo make clean - clean up the devlopment environment
	@echo make release - create a new release and upload it to PyPI

.PHONY: release
release: dist
	$(DEVENV)/bin/pip install twine
	$(DEVENV)/bin/twine upload dist/*

.PHONY: sysdeps
sysdeps:
	sudo apt install -y $(SYSDEPS)

.PHONY: test
test: dev
	$(DEVENV)/bin/python -m unittest discover . -v
