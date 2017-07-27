
## Using

1. If you're using the latest stable release of DC/OS, then download the [local-universe]
(https://downloads.mesosphere.com/universe/public/local-universe.tar.gz) container to each of your
masters. Otherwise, you'll need to build the container for your DC/OS version (see the "Building
Your Own" section below) and copy it to each of your masters.

1. Load the container into the local docker instance on each master:

    ```bash
    $ docker load < local-universe.tar.gz
    ```

1. Add the [`dcos-local-universe-http.service`](dcos-local-universe-http.service) definition to
each of your masters at `/etc/systemd/system/dcos-local-universe-http.service` and then start it.

    ```bash
    $ cp dcos-local-universe-http.service /etc/systemd/system/dcos-local-universe-http.service
    $ systemctl daemon-reload
    $ systemctl start dcos-local-universe-http
    ```

1. Add the [`dcos-local-universe-registry.service`](dcos-local-universe-registry.service)
definition to each of your masters at `/etc/systemd/system/dcos-local-universe-registry.service`
and then start it.

    ```bash
    $ cp dcos-local-universe-registry.service /etc/systemd/system/dcos-local-universe-registry.service
    $ systemctl daemon-reload
    $ systemctl start dcos-local-universe-registry
    ```

1. Remove the built in repositories from the host that you have the DCOS-CLI installed on
(alternatively, these can be removed from the DCOS UI under System>Repositories).

    ```bash
    $ dcos package repo remove Universe
    $ dcos package repo remove Universe-1.7
    ```

1. Add the local repository by using the DCOS-CLI.

    ```bash
    $ dcos package repo add local-universe http://master.mesos:8082/repo
    ```

1. To pull from this new repository, you'll need to setup the docker daemon on every agent to have
a valid SSL certificate. To do this, on every agent in your cluster, run the following:

    ```bash
    $ mkdir -p /etc/docker/certs.d/master.mesos:5000
    $ curl -o /etc/docker/certs.d/master.mesos:5000/ca.crt http://master.mesos:8082/certs/domain.crt
    $ systemctl restart docker
    ```

    Note that you're welcome to use the instructions for insecure registries instead of this step.
    We don't recommend this.

### FAQ

- I can't install CLI subcommands.

    Packages are being hosted at `master.mesos:8082`. If you cannot resolve (or connect) to that
    from your DC/OS CLI install, you won't be able to install subcommands. If you're able to
    connect to port 8082 on your masters, the easiest way around this is adding the IP for one of
    the masters to `/etc/hosts`.  See also [Outside Resources](#outside-resources) below.

- The images are broken!

    We host everything from inside your cluster, including the images. They're getting served up by
    `master.mesos:8082`. If you have connectivity to that IP, you can add it to `/etc/hosts` and
    get the images working.   See also [Outside Resources](#outside-resources) below.

- I don't see the package I was looking for!

    By default, we only bundle the `selected` packages. If you'd like to include something else,
    please see the "Building Your Own" section below.

## Building Your Own

1. Both nginx and the docker registry get bundled into the same container. This requires building
the "universe-base" container before you actually compile the universe container.

    ```bash
    $ sudo make base
    ```

1. Once you've built the "universe-base" container, you'll be able to create a local-universe one.
To keep size and time down, it is common to select only what you'd like to see. By default,
`selected` applications are the only ones included. You can pass a list in if you'd like to see
something more than that.

    ```bash
    $ sudo make DCOS_VERSION=<your DC/OS version> local-universe
    ```

    If you want to specify the set of package names and versions that get included in the image you
    can user the `DCOS_PACKAGE_INCLUDE variable. For example, to include two versions for Cassandra
    and one version of Marathon you can execute the following command.

    ```bash
    $ sudo make DCOS_VERSION=<your DC/OS version> DCOS_PACKAGE_INCLUDE="cassandra:1.0.25-3.0.10,cassandra:1.0.24-3.0.10,marathon:1.4.2" local-universe
    ```

### Building Your Own, off a non-changing universe-static base image.

Mesosphere provides a `mesosphere/universe-static` Docker image, which has all of the core
requirements to run a local universe.  All that must be added are your own certificates and repo
contents.

1. Use the make command to download the static image

    ```bash
    $ sudo make static-online
    ## Will pull and re-tag mesosphere/universe-static to universe-static
    ```

1. Create your certs (either use `make certs` or generate your own), and add them to the static
image to create a `universe-base` image

    ```bash
    $ sudo make static-base
    ## Will add certs to universe-static and create universe-base
    ```

1. Add content (see above)

    ```bash
    $ sudo make DCOS_VERSION=<your DC/OS version> local-universe
    ```

To generate your own static image, use and/or modify the make target `static-build` (e.g.,
`make static-build` instead of `make static-online`)

This leaves three total options:

```bash
make base
make DCOS_VERSION=<your DC/OS version> local-universe
```

```bash
make static-online
make static-base
make DCOS_VERSION=<your DC/OS version> local-universe
```

```bash
make static-build
make static-base
make DCOS_VERSION=<your DC/OS version> local-universe
```

### Building an old version of Local Universe
The latest version of Local Universe has changed directory structure in a way that is not
compatible with the old version of Local Universe. If you are interested in creating an old version
of Local Universe with the old directory structure you must use the following command instead of
the `local-universe` make target describe previously.

```bash
$ sudo make DCOS_VERSION=<your DC/OS version> old-local-universe
```

### Outside Resources

As a workaround for the image and CLI resource issues in [the FAQ above](#faq), you can place those
assets outside of the cluster.

1. Place your CLI and image resources on a web server accessible to CLI and web UI users.

2. Edit the URLs in the `resource.json` file of your package of interest to point to each of those
resources, in the `images` and `cli` sections.

3. Edit Makefile so the call to `local-universe.py` includes arguments `--nonlocal_images` and
`--nonlocal_cli`.

4. Proceed with [Building Your Own](#building-your-own) as above.

## Running Local Universe as a Marathon Service

Instead of deploying to each of your masters, you can easily run a local universe as a regular
Marathon service.

1. Edit Makefile so the call to `local-universe.py` includes the `--server_url` argument indicating
your choice of internal service name and port. For example, if you want dev-universe, then add
`--server_url http://dev-universe.marathon.mesos:8085`.

2. Build a container as per [Building Your Own](#building-your-own) above.

3. Deploy the container to your cluster as you would one of your regular apps.

4. Launch a single instance of your universe service, specifying health checks. Here's an example
Marathon app:

```json
{
  "id": "/dev-universe",
  "instances": 1,
  "cpus": 0.25,
  "mem": 128,
  "requirePorts": true,
  "container": {
    "type": "DOCKER",
    "docker": {
      "network": "BRIDGE",
      "image": "your_image_location:latest",
      "forcePullImage": true,
      "portMappings": [
        {
          "containerPort": 80,
          "hostPort": 8085,
          "protocol": "tcp"
        }
      ]
    },
    "volumes": []
  },
  "cmd": "nginx -g 'daemon off;'",
  "fetch": [ ],
  "healthChecks": [
    {
      "gracePeriodSeconds": 120,
      "intervalSeconds": 30,
      "maxConsecutiveFailures": 3,
      "path": "/repo-empty-v3.json",
      "portIndex": 0,
      "protocol": "HTTP",
      "timeoutSeconds": 5
    }
  ],
  "constraints": [
    [
      "hostname",
      "UNIQUE"
    ]
  ]
}
```

## Making changes...

###  ...to the `universe-static` image

1. Update `Dockerfile.static` with the changes
1. Bump the default value of `static_version` in `Makefile`
1. Create a pull request with the above changes
1. Once it is merged, run the [Publish universe-static image](https://teamcity.mesosphere.io/viewType.html?buildTypeId=Oss_Universe_2_PublishUniverseStaticImage&branch_Oss_Universe_2=%3Cdefault%3E&tab=buildTypeStatusDiv) build, providing the new version number when prompted
1. Submit a pull request that updates the `FROM universe-static:...` line in
`Dockerfile.static.base` to use the new version
