box:
	git archive --format tar -o ac-cloud.box HEAD

install: box
	vagrant box add -f --name ac-cloud ac-cloud.box

clean:
	rm ac-cloud.box