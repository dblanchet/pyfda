
GETTEXT = ~/Downloads/pygettext.py

BUNDLE_NAME = PyFlyDreamAltimeter
BUNDLE_SHORT_VERSION = 0.1
BUNDLE_IDENTIFIER = fr.free.blanchet.david
BUNDLE_INFO_STRING = $(BUNDLE_NAME) $(BUNDLE_SHORT_VERSION)
BUNDLE_VERSION = $(BUNDLE_NAME) $(BUNDLE_SHORT_VERSION)


langtemplate:
	$(GETTEXT) -o gui/lang.pot gui/*.py

test:
	python -m unittest discover

vtest:
	python -m unittest discover -v

cov coverage:
	coverage run --omit=*/site-packages/*,test* -m unittest discover
	coverage report
	coverage html
	echo "See coverage details in htmlcov/ subdir"

clean:
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
	rm -rf $(BUNDLE_NAME).app

macos_bundle:
	mkdir $(BUNDLE_NAME).app
	mkdir $(BUNDLE_NAME).app/Contents
	mkdir $(BUNDLE_NAME).app/Contents/MacOS
	mkdir $(BUNDLE_NAME).app/Contents/Resources

	cp tool/Info.plist.tmpl $(BUNDLE_NAME).app/Contents/Info.plist
	sed -i '' 's/BUNDLE_INFO_STRING/$(BUNDLE_INFO_STRING)/' $(BUNDLE_NAME).app/Contents/Info.plist
	sed -i '' 's/BUNDLE_IDENTIFIER/$(BUNDLE_IDENTIFIER)/' $(BUNDLE_NAME).app/Contents/Info.plist
	sed -i '' 's/BUNDLE_NAME/$(BUNDLE_NAME)/' $(BUNDLE_NAME).app/Contents/Info.plist
	sed -i '' 's/BUNDLE_SHORT_VERSION/$(BUNDLE_SHORT_VERSION)/' $(BUNDLE_NAME).app/Contents/Info.plist
	sed -i '' 's/BUNDLE_VERSION/$(BUNDLE_VERSION)/' $(BUNDLE_NAME).app/Contents/Info.plist

	cp tool/PkgInfo $(BUNDLE_NAME).app/Contents

	cp pyfda.py $(BUNDLE_NAME).app/Contents/MacOS/
	cp pyfdagui.py $(BUNDLE_NAME).app/Contents/MacOS/

	cp -r flydream $(BUNDLE_NAME).app/Contents/MacOS/
	cp -r gui $(BUNDLE_NAME).app/Contents/MacOS/

	cp tool/PyFda.icns $(BUNDLE_NAME).app/Contents/Resources/

