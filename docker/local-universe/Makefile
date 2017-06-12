REPO_BASE_DIR ?= $(shell pwd -P)/../..
.PHONY: certs base clean

certs:
	mkdir certs && openssl req					\
		-newkey rsa:4096 -nodes -sha256 -keyout certs/domain.key	\
		-x509 -days 365 -out certs/domain.crt			\
		-subj "/CN=master.mesos"

base: clean certs
	docker build -t universe-base -f Dockerfile.base .

clean:
	rm -rf certs &&							\
	rm -f local-universe.tar.gz || 0

static-build:
	docker build -t universe-static:0.2 -f Dockerfile.static .

static-online:
	docker pull mesosphere/universe-static:0.2 && \
		docker tag mesosphere/universe-static:0.2 universe-static:0.2

static-base:
	docker build -t universe-base -f Dockerfile.static.base .

local-universe: clean
	python3 $(REPO_BASE_DIR)/scripts/local-universe.py			\
		--repository $(REPO_BASE_DIR)/repo/packages/	\
		--selected &&							\
	docker save -o local-universe.tar mesosphere/universe:latest &&		\
	gzip local-universe.tar
