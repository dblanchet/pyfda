
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
