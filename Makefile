%.box:
	git archive --format tar -o $@ HEAD
	echo "{\"provider\":\"$(basename $@)\"}" > $@.tmp.json
	tar rf $@ $@.tmp.json --transform "s|$@.tmp.json|metadata.json|"
	rm $@.tmp.json


install: box
	vagrant box add -f --name $(shell git symbolic-ref --short HEAD) ac-cloud.box

clean:
	rm ac-cloud.box
