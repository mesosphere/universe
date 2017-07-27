REPO_BASE_DIR ?= $(shell pwd -P)/../..
static_version ?= 0.2-2
static_image ?= universe-static:$(static_version)

.PHONY: certs base clean gen-universe

certs:
	mkdir certs && openssl req \
		-newkey rsa:4096 -nodes -sha256 -keyout certs/domain.key \
		-x509 -days 365 -out certs/domain.crt \
		-subj "/CN=master.mesos"

base: clean certs
	docker build -t universe-base -f Dockerfile.base .

clean:
	rm -rf certs
	rm -f local-universe.tar.gz

static-build:
	docker build -t $(static_image) -f Dockerfile.static .

static-online:
	docker pull mesosphere/$(static_image)
	docker tag mesosphere/$(static_image) $(static_image)

static-base:
	docker build -t universe-base -f Dockerfile.static.base .

ifdef DCOS_PACKAGE_INCLUDE
gen-universe: clean
	python3 $(REPO_BASE_DIR)/scripts/local-universe.py \
		--repository $(REPO_BASE_DIR)/repo/packages/ \
		--include "$(DCOS_PACKAGE_INCLUDE)" \
		--dcos_version "$(DCOS_VERSION)"
else
gen-universe: clean
	python3 $(REPO_BASE_DIR)/scripts/local-universe.py \
		--repository $(REPO_BASE_DIR)/repo/packages/ \
		--selected \
		--dcos_version "$(DCOS_VERSION)"
endif

local-universe: gen-universe clean
	docker save -o local-universe.tar mesosphere/universe:latest
	gzip local-universe.tar

old-local-universe: clean
	python3 $(REPO_BASE_DIR)/scripts/old-local-universe.py \
		--repository $(REPO_BASE_DIR)/repo/packages/ \
		--selected \
		--dcos_version "$(DCOS_VERSION)"
	docker save -o local-universe.tar mesosphere/universe:latest
	gzip local-universe.tar
