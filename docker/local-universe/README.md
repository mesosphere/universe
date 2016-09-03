
## Using

1. For each of your masters, download the [local-universe](https://downloads.mesosphere.com/universe/public/local-universe.tar.gz) container to them.

1. Load the container into the local docker instance on each master:

    ```bash
    $ docker load < local-universe.tar.gz
    ```

1. Add the [`dcos-local-universe-http.service`](dcos-local-universe-http.service) definition to each of your masters at `/etc/systemd/system/dcos-local-universe-http.service` and then start it.

    ```bash
    $ cp dcos-local-universe-http.service /etc/systemd/system/dcos-local-universe-http.service
    $ systemctl daemon-reload
    $ systemctl start dcos-local-universe-http
    ```

1. Add the [`dcos-local-universe-registry.service`](dcos-local-universe-registry.service) definition to each of your masters at `/etc/systemd/system/dcos-local-universe-registry.service` and then start it.

    ```bash
    $ cp dcos-local-universe-registry.service /etc/systemd/system/dcos-local-universe-registry.service
    $ systemctl daemon-reload
    $ systemctl start dcos-local-universe-registry
    ```

1. Remove the built in repositories from the host that you have the DCOS-CLI installed on (alternatively, these can be removed from the DCOS UI under System>Repositories).

    ```bash
    $ dcos package repo remove Universe
    $ dcos package repo remove Universe-1.7
    ```

1. Add the local repository by using the DCOS-CLI.

    ```bash
    $ dcos package repo add local-universe http://master.mesos:8082/repo
    ```

1. To pull from this new repository, you'll need to setup the docker daemon on every agent to have a valid SSL certificate. To do this, on every agent in your cluster, run the following:

    ```bash
    $ mkdir -p /etc/docker/certs.d/master.mesos:5000
    $ curl -o /etc/docker/certs.d/master.mesos:5000/ca.crt http://master.mesos:8082/certs/domain.crt
    $ systemctl restart docker
    ```

    Note that you're welcome to use the instructions for insecure registries instead of this step. We don't recommend this.

### FAQ

- I can't install CLI subcommands.

    Packages are being hosted at `master.mesos:8082`. If you cannot resolve (or connect) to that from your DC/OS CLI install, you won't be able to install subcommands. If you're able to connect to port 8082 on your masters, the easiest way around this is adding the IP for one of the masters to `/etc/hosts`.

- The images are broken!

    We host everything from inside your cluster, including the images. They're getting served up by `master.mesos:8082`. If you have connectivity to that IP, you can add it to `/etc/hosts` and get the images working.

- I don't see the package I was looking for!

    By default, we only bundle the `selected` packages. If you'd like to get something else, run the build your own instructions yourself.

## Building Your Own

1. Both nginx and the docker registry get bundled into the same container. This requires building the "universe-base" container before you actually compile the universe container.

    ```bash
    $ sudo make base
    ```

1. Once you've build the "universe-base" container, you'll be able to create a local-universe one. To keep size and time down, it is common to select only what you'd like to see. By default, `selected` applications are the only ones included. You can pass a list in if you'd like to see something more than that.

    ```bash
    $ sudo make local-universe
    ```
