DEVENV=devenv
SYSDEPS=build-essential python3-virtualenv tox

all: help

dev:
	tox -e $(DEVENV)

check:
	tox

clean:
	rm -rf $(DEVENV) .tox

help:
	@echo make dev - create the development environment
	@echo make test - run unit tests
	@echo make check - run lint and tests on the resulting packages
	@echo make clean - clean up the devlopment environment

sysdeps:
	sudo apt install -y $(SYSDEPS)

test:
	$(DEVENV)/bin/py.test -s --tb=native -v tests
