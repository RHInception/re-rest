########################################################

# Makefile for re-rest
#
# useful targets (not all implemented yet!):
#   make clean ------------------- Clean up garbage
#   make pyflakes/pep8/coverage -- source code checks
#   make tests ------------------- run all unit tests (export LOG=true for /tmp/ logging)

########################################################

# > VARIABLE = value
#
# Normal setting of a variable - values within it are recursively
# expanded when the variable is USED, not when it's declared.
#
# > VARIABLE := value
#
# Setting of a variable with simple expansion of the values inside -
# values within it are expanded at DECLARATION time.

########################################################

# # This doesn't evaluate until it's called. The -D argument is the
# # directory of the target file ($@), kinda like `dirname`.
# ASCII2MAN = a2x -D $(dir $@) -d manpage -f manpage $<
# MANPAGES := docs/man/man1/re-rest.1

NAME := rerest
PKGNAME := re-rest
RPMSPECDIR := ./contrib/rpm
RPMSPEC := $(RPMSPECDIR)/$(PKGNAME).spec
# VERSION file provides one place to update the software version.
VERSION := $(shell cat VERSION)
RPMRELEASE = $(shell awk '/global _short_release/{print $$NF; exit}' $(RPMSPEC).in)


# Build the spec file on the fly. Substitute version numbers from the
# # canonical VERSION file.
re-rest.spec: $(RPMSPECDIR)/re-rest.spec.in
	sed "s/%VERSION%/$(VERSION)/" $< > $@


# Build the distutils setup file on the fly.
setup.py: setup.py.in VERSION $(RPMSPECDIR)/re-rest.spec.in
	sed -e "s/%VERSION%/$(VERSION)/" -e "s/%RELEASE%/$(RPMRELEASE)/" $< > $@


# # To force a rebuild of the docs run 'touch VERSION && make docs'
# docs: $(MANPAGES)

# # Regenerate %.1.asciidoc if %.1.asciidoc.in has been modified more
# # recently than %.1.asciidoc.
# %.1.asciidoc: %.1.asciidoc.in VERSION
# 	sed "s/%VERSION%/$(VERSION)/" $< > $@

# # Regenerate %.1 if %.1.asciidoc or VERSION has been modified more
# # recently than %.1. (Implicitly runs the %.1.asciidoc recipe)
# %.1: %.1.asciidoc
# 	$(ASCII2MAN)

tag:
	git tag -s -m $(TAG) $(TAG)

tests: coverage pep8 pyflakes
	:

coverage:
	@echo "#############################################"
	@echo "# Running Unit + Coverage Tests"
	@echo "#############################################"
	nosetests -v --with-cover --cover-min-percentage=80 --cover-package=rerest --cover-html test/

clean:
	@find . -type f -regex ".*\.py[co]$$" -delete
	@find . -type f \( -name "*~" -or -name "#*" \) -delete
	@rm -fR build cover dist rpm-build MANIFEST htmlcov .coverage rerest.egg-info

pep8:
	@echo "#############################################"
	@echo "# Running PEP8 Compliance Tests"
	@echo "#############################################"
	pep8 --ignore=E501,E121,E124 src/rerest/

pyflakes:
	@echo "#############################################"
	@echo "# Running Pyflakes Sanity Tests"
	@echo "# Note: most import errors may be ignored"
	@echo "#############################################"
	-pyflakes src/rerest

install: clean
	python ./setup.py install

sdist: setup.py clean
	python setup.py sdist -t MANIFEST.in

rpmcommon: re-rest.spec sdist
	@mkdir -p rpm-build
	@cp dist/$(NAME)-$(VERSION)-$(RPMRELEASE).tar.gz rpm-build/$(VERSION)-$(RPMRELEASE).tar.gz

srpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	-bs $(RPMSPEC)
	@echo "#############################################"
	@echo "$(PKGNAME) SRPM is built:"
	@find rpm-build -maxdepth 2 -name '$(PKGNAME)*src.rpm' | awk '{print "    " $$1}'
	@echo "#############################################"

rpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	-ba $(RPMSPEC)
	@echo "#############################################"
	@echo "$(PKGNAME) RPMs are built:"
	@find rpm-build -maxdepth 2 -name '$(PKGNAME)*.rpm' | awk '{print "    " $$1}'
	@echo "#############################################"
