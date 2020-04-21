PYTHON_SET_UP = /bin/python setup.py
PIP = /bin/pip
PIP_INSTALL_FLAG = --user
SYSTEMCTL = /bin/systemctl --user
SYSTEMDDIR = $(PWD)/systemd
CONFIGDIR = $(HOME)/.config/systemd/user
CP = cp

dist = sdist bdist_wheel
pkg = clashcli
systemdfiles = $(addprefix $(CONFIGDIR)/$(pkg), .service .timer)

install_all: install timer

dist: $(dist)

$(CONFIGDIR)/%: $(SYSTEMDDIR)/%
	$(CP) $< $@

install:
	@$(PIP) install . $(PIP_INSTALL_FLAG)

dev:
	@$(PIP) install -e . $(PIP_INSTALL_FLAG)

timer: $(systemdfiles)
	@$(SYSTEMCTL) enable $(pkg).timer

uninstall:
	@$(PIP) uninstall $(pkg)
	@-$(SYSTEMCTL) disable $(pkg).timer
	@-$(RM) $(systemdfiles)

$(dist):
	$(PYTHON_SET_UP) $@

clean:
	-$(RM) -r  build dist *.egg-info
