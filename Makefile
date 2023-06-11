MDFILES = \
	./demo1-linux-bridge/index.md \
	./demo2-podman-networking/index.md \
	./demo3-openvswitch/index.md

HTMLFILES = $(MDFILES:.md=.html)

%.html: %.md
	pandoc --toc --standalone -c style/common.css -o $@ $<

all: slides.html $(HTMLFILES)

clean:
	rm -f slides.html $(HTMLFILES)

serve:
	python -m http.server > access_log 2>&1

.PHONY: scripts
scripts:
	mkdir -p scripts
	py extract-fenced.py -o scripts demo*/index.md -v
