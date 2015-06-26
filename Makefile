box:
	git archive --format tar -o ac-cloud.box HEAD

install: box
	vagrant box add -f --name $(shell git symbolic-ref --short HEAD) ac-cloud.box

clean:
	rm ac-cloud.box
