ac-cloud.box:
	git archive --format tar -o ac-cloud.box HEAD

install: ac-cloud.box
	vagrant box add -f --name multi_exp ac-cloud.box

clean:
	rm ac-cloud.box
