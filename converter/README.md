# Universe Converter

Wiki : https://wiki.mesosphere.com/display/OPS/Universe+Converter+Service


### Testing

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
4. Once the app is healthy, we can ssh to one of the nodes and execute bunch of curl calls. Here is a sample : 

```bash
# Export a stub url you want to test.
STUB_UNIVERSE_URL=<Any_stub_url>

# Test all the happy paths.
for i in v5,1.13 v5,1.12 v4,1.13 v4,1.12 v4,1.11 v4,1.10 v3,1.9; do
    IFS=',' read packaging_version dcos_version <<< "${i}"
    echo "Testing ${packaging_version} for ${dcos_version}"
    curl -f -X GET "http://transform.marathon.mesos:8086/transform?url=${STUB_UNIVERSE_URL}" \
         -H "Accept: application/vnd.dcos.universe.repo+json;charset=utf-8;version=${packaging_version}" \
         -H "User-Agent: cosmos/0.6.0 dcos/${dcos_version}" \
         -o /dev/null
done
```
