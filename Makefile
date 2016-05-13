.PHONY: certs base clean

certs:
	mkdir docker/certs && openssl req					\
		-newkey rsa:4096 -nodes -sha256 -keyout docker/certs/domain.key	\
		-x509 -days 365 -out docker/certs/domain.crt			\
		-subj "/CN=master.mesos"

base: clean certs
	cd docker && docker build -t universe-base -f Dockerfile.base .

clean:
	rm -rf docker/certs &&							\
	rm -f local-universe.tar.gz || 0

local-universe: clean
	python3 scripts/local-universe.py --repository repo/packages/	\
		--selected &&							\
	docker save -o local-universe.tar mesosphere/universe:latest &&	\
	gzip local-universe.tar

