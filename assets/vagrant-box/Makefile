%.box: .git/COMMIT_EDITMSG
	git archive --format tar -o $@ HEAD
	echo "{\"provider\":\"$(basename $@)\"}" > $@.tmp.json
	chown gothm:student $@.tmp.json
	tar rf $@ $@.tmp.json --transform "s|$@.tmp.json|metadata.json|"
	rm $@.tmp.json

metadata.json: aws.box azure.box
	python metadata.py aws azure > metadata.json

install: metadata.json
	vagrant box add metadata.json -f --provider aws
	vagrant box add metadata.json -f --provider azure

clean:
	rm -f *.box *.box.tmp.json metadata.json
