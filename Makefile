SHELL=/bin/bash
export ENV=dev

.PHONY: python-dependencies
python-dependencies:
	pip3 install -r requirements.txt

.PHONY: test-docker
test-docker:
	pip3 install -r requirements.txt && cd ./assignment && python3 manage.py test

.PHONY: test
test:
	docker-compose up --build wikiracer-test 

# must have python3.7 installed
.PHONY: test-local
test-local:
	pip3 install -r requirements.txt && cd ./assignment && python3 manage.py test 

.PHONY: run-local
run-local:
	docker build -t wikiracer . && docker run -p 8000:8000 -t wikiracer 

.PHONY: run
run:
	docker-compose up --build wikiracer-prod
