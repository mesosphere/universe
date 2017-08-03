DOCKER_TAG?=0.0.2
DOCKER_IMAGE?=localhost:5000/mesosphere/universe-rakuten

build:
	scripts/build.sh
	DOCKER_TAG="$(DOCKER_TAG)" DOCKER_IMAGE="$(DOCKER_IMAGE)" docker/server/build.bash

push:
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)

local_deploy:
	docker run -d -p 8500:80 $(DOCKER_IMAGE):$(DOCKER_TAG)

dcos_deploy:
	dcos marathon app add docker/server/target/marathon.json
