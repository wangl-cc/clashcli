PYTHON_SET_UP = /bin/python setup.py
PIP = /bin/pip
INSTALL_FLAG = --user

dist = sdist bdist_wheel
pkg = clashcli

dist: $(dist)

install:
	$(PIP) install . $(INSTALL_FLAG)

dev:
	$(PIP) install -e . $(INSTALL_FLAG)

uninstall:
	$(PIP) uninstall $(pkg)

$(dist):
	$(PYTHON_SET_UP) $@

clean:
	-$(RM) -r  build dist *.egg-info
