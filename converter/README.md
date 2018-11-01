# Universe Converter

Wiki : https://wiki.mesosphere.com/display/OPS/Universe+Converter+Service


### Testing

Converter is an internal tool used for our CI only. Currently, we do not have any automated tests but the following manual testing can be performed whenever there is an update to converter service.

1. Build a docker image for the converter locally with something like : 

```bash
DOCKER_IMAGE="<your_org>/universe-converter"  DOCKER_TAG="dev" ./converter/build.bash
docker push "<your_org>/universe-converter:dev"
```

2. The docker build should have generated a `target/marathon.json`
3. Use the above marathon app defintion to launch a marathon app in any cluster. If testing from outside the cluster, these labels need to be added :
```
     "DCOS_SERVICE_NAME": "transform",
     "DCOS_SERVICE_SCHEME": "http",
     "DCOS_SERVICE_PORT_INDEX": "0"
```
4. Once the app is healthy, we can ssh to one of the nodes and execute bunch of curl calls. Testing from inside the cluster when we do not want to account for downstream latencies/glitches.

```bash
#!/usr/bin/env bash

function info { echo "[info] $@" ;}

# Export a stub url you want to test.
: ${CONVERTER_URL?"Need to set CONVERTER_URL"}

# Test all the happy paths.
for i in v5,1.13 v5,1.12 v4,1.13 v4,1.12 v4,1.11 v4,1.10 v3,1.9; do
    IFS=',' read packaging_version dcos_version <<< "${i}"
    info "Testing ${packaging_version} for ${dcos_version}"
    curl -s -f -X GET "${CONVERTER_URL}" \
        -H "Accept: application/vnd.dcos.universe.repo+json;charset=utf-8;version=${packaging_version}" \
        -H "User-Agent: cosmos/does-not-matter dcos/${dcos_version}" \
        -H "Authorization: ${AUTHORIZATION_HEADER}" \
        -o /dev/null
done


if [ -z "$RUN_LOAD_TESTS" ]; then
    info "Skipping load tests as RUN_LOAD_TESTS is not set"
else
    DEFAULT_ITERATIONS=${DEFAULT_ITERATIONS:-10}
    packaging_version="v5"
    dcos_version="1.13"
    info "Running load tests"
    for i in `eval echo {0..$DEFAULT_ITERATIONS}`; do
        info "Iteration $i"
        curl -s -f -X GET "${CONVERTER_URL}" \
            -H "Accept: application/vnd.dcos.universe.repo+json;charset=utf-8;version=${packaging_version}" \
            -H "Authorization: ${AUTHORIZATION_HEADER}" \
            -H "User-Agent: cosmos/does-not-matter dcos/${dcos_version}" \
            -o /dev/null
    done
fi
```

5. Also, make sure that the converter url can be added to cosmos via `dcos package repo add <some_name> <converter_url>`.
