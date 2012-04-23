#	$Id: Makefile 38 2011-08-13 09:50:01Z georgesk $	

DESTDIR =

LRELEASE = lrelease-qt4
LUPDATE = pylupdate4

SOURCES = $(shell ls *.py| grep -v Ui_)
INTERFACES = $(shell ls *.ui)
PY_INTERFACES = $(patsubst %.ui, Ui_%.py, $(INTERFACES))

all: $(PY_INTERFACES) lang

lang:
	cd lang; $(LUPDATE) uicilibris.pro; $(LRELEASE) *.ts

svn-propset:
	svn propset svn:keywords "Id" $(SOURCES) $(INTERFACES) Makefile

clean:
	rm -f *~ *.pyc essai.* $(PY_INTERFACES)
	cd plugin; rm -f *~ *.pyc
	cd lang; rm -f *~ *.qm
	cd plugin_collection; rm -f *~ *.pyc

Ui_%.py: %.ui
	pyuic4 $< > $@

install:

URL_TEST = http://localhost/mediawiki/index.php/Essai_nécessaire_pour_le_développement_de_Wiki2many

#URL_TEST = http://localhost/mediawiki/index.php/ExpEYES

test:
	python __init__.py $(URL_TEST)

.PHONY: all clean install test svn-propset lang
