
GETTEXT = ~/Downloads/pygettext.py


langtemplate:
	$(GETTEXT) -o gui/lang.pot gui/*.py

test: test2 test3

test2:
	python2.7 -m unittest discover

test3:
	python3 -m unittest discover

cov coverage:
	coverage run --omit=*/site-packages/*,test* -m unittest discover
	coverage report
	coverage html
	echo "See coverage details in htmlcov/ subdir"

include Makefile.macos

.PHONY: clean
clean: clean-mac
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -f `find . -type f -name '@*' `
	rm -f `find . -type f -name '#*#' `
	rm -f `find . -type f -name '*.orig' `
	rm -f `find . -type f -name '*.rej' `
	rm -rf dist
	rm -f .coverage
	rm -rf htmlcov
	rm -rf build
	rm -f MANIFEST

