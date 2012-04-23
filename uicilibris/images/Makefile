DESTDIR = 

SOURCES = uicilibris.svg

TARGETS = $(patsubst %.svg, %-64px.png, $(SOURCES))

all: $(TARGETS)

clean:
	rm -f $(TARGETS) *~

%-64px.png: %.svg
	rsvg -w 64 $< $@

install:
	install -d $(DESTDIR/images)
	install -m 644 $(TARGETS) $(DESTDIR/images)

.PHONY: all clean install
