MDFILES = \
	./demo1-linux-bridge/index.md \
	./demo2-podman-networking/index.md \
	./demo3-openvswitch/index.md

HTMLFILES = $(MDFILES:.md=.html)

SCRIPTS = $(shell py extract-fenced.py -o scripts -l $(MDFILES))

%.html: %.md
	pandoc --toc --standalone -c style/common.css -o $@ $<

all: slides.html $(HTMLFILES)

clean:
	rm -f slides.html $(HTMLFILES)

serve:
	python -m http.server > access_log 2>&1

scripts: $(SCRIPTS)

$(SCRIPTS): $(MDFILES)
	mkdir -p scripts
	py extract-fenced.py -o scripts -v $(MDFILES)

upload-scripts: scripts
	vagrant status --machine-readable | awk -F, '/state,running/ {print $$2}' | \
		xargs -iNODE sh -c 'tar -cf- . | vagrant ssh NODE -- tar -xf-'
