DESTDIR =
SOURCES = $(ls uicilibris/*.py uicilibris/uicilibris config.dox)

all:
	make -C uicilibris $@

uicilibris.1: manpage.xml
	xsltproc --nonet \
          --param man.charmap.use.subset "0" \
          --param make.year.ranges "1" \
          --param make.single.year.ranges "1" \
          /usr/share/xml/docbook/stylesheet/docbook-xsl/manpages/docbook.xsl \
          $<
clean:
	rm -f *~
	rm -rf doc/*
	make -C uicilibris $@

doc: force
	$(MAKE) doc/html/index.html 

doc/html/index.html: $(SOURCES)
	doxygen config.dox

install:
	install -d $(DESTDIR)/usr/share/
	cp -a uicilibris $(DESTDIR)/usr/share/
	cp -a guide $(DESTDIR)/usr/share/uicilibris
	install -d $(DESTDIR)/usr/share/uicilibris/lang
	install -m 644 uicilibris/lang/*.qm $(DESTDIR)/usr/share/uicilibris/lang
	[ -f "guide/Poor_man_s_user_guide_for_UICI_LIBRIS.html" ] && \
	  ln -s "Poor_man_s_user_guide_for_UICI_LIBRIS.html" $(DESTDIR)/usr/share/uicilibris/guide/index.html
	rm -f $(DESTDIR)/usr/share/uicilibris/images/COPYING
	install -d $(DESTDIR)/usr/bin
	echo '#!/bin/sh' > $(DESTDIR)/usr/bin/uicilibris
	echo 'cd /usr/share/uicilibris; exec ./uicilibris' >> $(DESTDIR)/usr/bin/uicilibris
	chmod +x $(DESTDIR)/usr/bin/uicilibris


.PHONY: all clean doc install force
