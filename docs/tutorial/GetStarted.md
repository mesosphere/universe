# Getting Started
This document is intended as a "getting started" guide. The audience are developers looking to modify or *publish* the packages to the Universe. This document is written in tutorial and walk-through format. The goal is to help you "get started". It does not go into great depth on some of the conceptual or inner details. This guide aims at making a user familiar with the concepts of what a Package is and what are the roles of Marathon and Universe in the package life cycle.

#### Table of Contents
- [Required nomenclature](#required-nomenclature)
	- [What is Universe?](#what-is-universe)
	- [What is Marathon?](#what-is-marathon)
	- [What is a package?](#what-is-a-package)
- [Prerequisites](#prerequisites)
	- [Library dependencies](#library-dependencies)
	- [Access requirements](#access-requirements)
	- [This repository](#this-repository)
- [Create a package](#create-a-package)
	- [Step 1 : Create a simple Python HTTP Server](#step-1-create-a-simple-python-http-server)
		- [Change port mapping to be dynamic](#change-port-mapping-to-be-dynamic)
	- [Step 2 : Creating a Docker container](#step-2-creating-a-docker-container)
		- [Build the container](#build-the-container)
		- [Test your container](#test-your-container)
		- [Tag and publish your container](#tag-and-publish-your-container)
	- [Step 3 : Creating a DC/OS Package](#step-3-creating-a-dcos-package)
		- [config.json](#configjson)
		- [resource.json](#resourcejson)
		- [package.json](#packagejson)
		- [marathon.json.mustache](#marathonjsonmustache)
	- [Step 4 : Testing the package](#step-4-testing-the-package)
		- [Validation using build script.](#validation-using-build-script)
		- [Build the local Universe server](#build-the-local-universe-server)
		- [Run the local Universe server](#run-the-local-universe-server)
		- [Add the Universe repo to DC/OS cluster:](#add-the-universe-repo-to-dcos-cluster)
		- [Install the package](#install-the-package)
	- [Step 5 : Publish the package](#step-5-publish-the-package)

## Required nomenclature
This guide assumes you are familiar with the basics of the concepts mentioned below. Advanced users can skip this section and jump to [Create a package](#create-a-package). If you are new to DC/OS, we recommend reading this section along with the external links provided.


### What is Universe?
The Universe is a DC/OS package repository that contains services like Spark, Cassandra, Jenkins, and many others. It allows users to install these services with a single click from the DC/OS UI or by a simple `dcos package install <package_name>` command from the DC/OS CLI. Many community members have already submitted their own packages to the Universe, and we encourage anyone interested to get involved with package development! It is a great way of contributing to the DC/OS ecosystem and allows users to easily get started with your favorite package.


### What is Marathon?
[Marathon](https://mesosphere.github.io/marathon/) is a production-grade container orchestration platform for Mesosphere’s Datacenter Operating System (DC/OS) and [Apache Mesos](https://mesos.apache.org/). In order to deploy applications on top of Mesos, one can use Marathon for Mesos. Marathon is a cluster-wide init and control system for running Linux services in cgroups and Docker containers. Marathon has a number of different deploy [features](https://mesosphere.github.io/marathon/#features) and is a very mature project. Marathon runs on top of Mesos, which is a highly scalable, battle tested and flexible resource manager. Marathon is proven to scale and runs in many production environments.


### What is a package?
There are several ways to deploy your service onto a running DC/OS cluster.
  * Use the DC/OS Marathon command in the CLI,
  * Use the Marathon REST API directly, or
  * Deploy your service as a package.

Deploying your service using the package approach makes your life easier and service management efficient. Once you have a running DC/OS cluster, you will be able to browse packages in the dashboard. A package consists of the four required configuration files(`config.json`, `package.json`, `resource.json`, and `marathon.json.mustache`) and all of the external files linked from them.

A package implicitly relies on Marathon; its contents are used to generate a Marathon app definition. By the end of this guide, you will be able to build, publish, and browse your package in the cluster.


## Prerequisites
Before starting this guide, make sure you have met the following conditions.

### Library dependencies
* [DC/OS CLI](https://dcos.io/docs/latest/cli/install/) installed and configured.
* [jq](https://stedolan.github.io/jq/download/) is installed in your environment.
* `python3` in your environment.
* Docker is installed.

### Access requirements
* Access to a running [DC/OS](https://dcos.io/install/).
* The Universe Server needs to be built and run in a location accessible by the DC/OS Cluster. There is no other way to test your package otherwise.
* Mesos needs access to the Docker registry that has your Universe Server. In our guide, we use Docker Hub as the registry.


### This repository
- Current packaging version is v4 and we follow this standard for this guide. This guide will be updated as and when we release a new version.
- The packages are located in `repo/packages` directory.
- This tutorial is in `tutorial` directory
- You can refer to **schemas** in `repo/meta/schema` directory. This directory has
  - `config-schema.json` that refers to the schema of the `config.json`
  - `package-schema.json` that refers to the schema of the `package.json`
  - `v3-resource-schema.json` that refers to the schema of the `resource.json` for the v3 and v4 packages
  - `*-repo-schema.json` files are not meant to be used by package developers; they instead define the schema for the API between Universe and DC/OS.

## Create a package
Let us build a simple Python HTTP server, which, when it receives an HTTP GET request, responds with the current time at the server. We will start with this and build a package that provides this Python server as a DC/OS service.


### Step 1 : Create a simple Python HTTP Server
For the purposes of this guide, we will be using Python 3 and the HTTPServer module provided by its standard library. Let's create a file called `helloworld.py` in an empty directory called `time-server-service`

```python
import time
import http.server
import os


HOST_NAME = '0.0.0.0' # Host name of the HTTP server
# Gets the port number from $PORT0 environment variable
PORT_NUMBER = 8000

class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(s):
        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write("<html><head><title>Time Server</title></head>")
        s.wfile.write("<body><p>The current time is {}</p>".format(time.asctime()))
        s.wfile.write("</body></html>")

if __name__ == '__main__':
    server_class = http.server.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print(time.asctime(), "Server Starts - {}:{}".format(HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), "Server Stops - {}:{}".format(HOST_NAME, PORT_NUMBER))
```

The code snippet simply starts a Python server and serves the GET requests with HTML that says the current time. You should be able to run this code snippet with `python3 helloworld.py` and browse [localhost:8000](http://localhost:8000).

#### Change port mapping to be dynamic

If we want to get a port number dynamically from available ports, Marathon provides a way to achieve this. We access the available ports using the environment variable `$PORT0`, `$PORT1`, `$PORT2` and so on. This will be explained clearly in a later section. But for now, just change your Python snippet to read the port from an environment variable as below :

```python
# Gets the port number from $PORT0 environment variable
PORT_NUMBER = int(os.environ['PORT0'])
```

Once you do this, you can browse your server after executing `PORT0=8000 python3 helloworld.py`

### Step 2 : Creating a Docker container
Creating a Docker container is essential to distribute _this_ service. It runs completely isolated from the host environment by default, only accessing host files and ports if configured to do so. To continue reading, you need to be familiar with Docker; we recommend this [get-started](https://docs.docker.com/get-started/) guide. You should have logged in to your Docker account in your terminal using `docker login`.

_Note: Giving a Docker image is optional and we can have other ways to execute the binary (E.g.: The package `cassandra` doesn't use a Docker image to install the binary.)._

We create a Docker file (named `Dockerfile`) in the `time-server-service` directory created earlier. The `Dockerfile` should look like this:

```
# Use an official Python runtime as a base image
FROM python:3

# Set the working directory to the package directory
WORKDIR /package

# Copy the current directory contents into the container at /package
ADD . /package

# Run helloworld.py when the container launches. -u flag makes sure the output is not buffered
CMD ["python3", "-u", "helloworld.py"]
```
Read through the comments to understand what each line in the `Dockerfile` does.


#### Build the container

*Throughout the rest of this guide, we refer to `docker-user-name` as your Docker user name where you access your Docker images from a registry such as Docker Hub. You are expected to replace the keyword `docker-user-name` with your Docker user name in all commands and files*

Now that we have everything ready, we can build our container. Here’s what `ls` should show:
```
$ ls
Dockerfile		helloworld.py
```
Now run the build command. This creates a Docker image which we’re going to tag using `-t` so it has a friendly name.

`docker build -t docker-user-name/time-server:part1 .`

Where is your built image? It's in your machine's local Docker daemon:

```
$ docker images

REPOSITORY                        TAG         IMAGE ID
docker-user-name/time-server      part1       42somsoc147
```


#### Test your container
When you execute `docker images`, you should be able to see the your image in the displayed list. In order to make sure the image is working as expected, you can run the container by issuing the below command :

`docker run -env PORT0=8000 -p 80:8000 -t docker-user-name/time-server:part1`

Note that we are reading the port number from the `PORT0` environment variable. Marathon sets this environment variable when launching the container and since we don't have that yet, we need to provide the environment variable manually using `-env PORT0=8000`. The `-p` option maps the host port 80 to the container port 8000. The  `-t` flag creates a pseudoTTY and since we unbuffered the Python standard I/O in our Dockerfile, we will be able to see the real time logs of the server in the console. Once you executed the above command, you should be able to browse [localhost](http://localhost:80).


#### Tag and publish your container
Once you are satisfied with the functionality of your container, you can publish the Docker image on to the Docker registry. In our case, we execute :

`docker tag time-server docker-user-name/time-server:part1`

This tags our `time-server` image with the Docker repository `time-server` in your Docker user name `docker-user-name` and provides an optional tag `part1`.

Once we tag our image, we have to publish (synonmous with `git push`) to the Docker registry so that Marathon will be able to discover this in the future using an URL. We achieve this by executing the command :

`docker push docker-user-name/time-server:part1`

Now that we have the container ready, in the next section we will see how to create a package!

### Step 3 : Creating a DC/OS Package
In order to create a package, you need to have forked the [Universe repo](https://github.com/mesosphere/universe) and then cloned it so that it is available in your terminal. Once you do this, create a directory named `time-server` under the `repo/package/T` directory (as our package name starts with the letter "t"). Inside this directory, if there is already another package with a name of your choice, you have to name your package differently. We create all the required files in this package.

After you read this step, if you need further examples, you can refer to the [repo/packages/H/hello-world](repo/packages/H/hello-world) package.

Each package has its own directory, with one subdirectory for each package revision. Each package revision directory contains the set of files necessary to create a consumable package that can be used by a DC/OS Cluster to install the package. For example, our package would look like this:

```
└── repo/package/T/time-server
    ├── 0
    │   ├── config.json
    │   ├── resource.json
    │   ├── marathon.json.mustache
    │   └── package.json
    └── ...
```

In our case, since this is the first version of our time-server, we will create the above directory structure with only one revision (with number 0) and create the required empty files. As the versions of your package grow, this number increments by one unit. Also, once package revision has been committed to Universe, it files should never be modified. A new revision must be created for any change.

***Tip : When reading the schema JSON files, look for `required` JSON field to understand what fields are mandatory***

#### config.json
As the name says, this file specifies how our package can be configured. This is how our `config.json` should look:

```
{
  "$schema": "http://json-schema.org/schema#",
  "properties": {
    "service": {
      "type": "object",
      "description": "DC/OS service configuration properties",
      "properties": {
        "name": {
          "description": "Name of this service instance",
          "type": "string",
          "default": "time-server"
        },
        "cpus": {
          "description": "CPU shares to allocate to each service instance.",
          "type": "number",
          "default": 0.1,
          "minimum": 0.1
        },
        "mem": {
          "description":  "Memory to allocate to each service instance.",
          "type": "number",
          "default": 256.0,
          "minimum": 128.0
        }
      }
    }
  }
}
```

We have three main properties to be configured. The `name` is the actual name of the service running in DC/OS. The `cpus` and `mem` are the amount of CPU and Memory required for each service instance. You can read more about the various fields in this file [here](https://github.com/mesosphere/universe#configjson) or can refer to [`repo/meta/schema/config-schema.json`](repo/meta/schema/config-schema.json) for a full fledged definition.

(Note : If you need to add a config property after your package revision has been committed to Universe, you have to bump your package version and create new package. So be sure to add all the config properties that you need.)

#### resource.json
This file contains all of the externally hosted resources (e.g. Docker images, HTTP objects and images) needed to install the application. It also contains the `cli` section that can be used to allow a package to configure native CLI subcommands for several platforms and architectures.

Below is the resource file that we use for our package. We have provided our earlier published `docker-user-name/time-server:part1` image under the `docker` JSON field here. Note that giving a Docker image is optional and we can have other ways to execute the binary. As mentioned earlier, The package `cassandra` doesn't use a Docker image to install the binary; instead, it tells Marathon to run a shell command. It has all the dependencies it needs because they are specified as URIs in `resource.json`

```
{
  "assets": {
    "container": {
      "docker": {
        "timeserverimage": "docker-user-name/time-server:part1"
      }
    }
  }
}
```

You can put the icons related to your package and screenshots of your service if needed here. You can read more about the various fields in this file [here](https://github.com/mesosphere/universe#resourcejson) or can refer to [`repo/meta/schema/v3-resource-schema.json`](repo/meta/schema/v3-resource-schema.json) for a full fledged definition.


#### package.json
Every package in Universe must have a `package.json` file which specifies the high level metadata about the package.

Below is a snippet that represents our time server `package.json` (a version `4.0` package). This JSON has only the mandatory fields configured. As this is our first version, we fill the version field to be 1.0.0

```
{
  "packagingVersion": "4.0",
  "name": "time-server",
  "version": "1.0.0",
  "maintainer": "https://github.com/mesosphere/universe",
  "description": "This is a simple Python HTTP server that displays a webpage that says the current time at the server location",
  "tags": ["python", "http", "time-server"]
}
```

Note that the version field specifies the version of the package and this is independent of the directory number inside the `time-server` directory.

You can read more about the various fields in this field [here](https://github.com/mesosphere/universe#configjson) or can see [`repo/meta/schema/package-schema.json`](repo/meta/schema/package-schema.json) for the full JSON schema outlining what properties are available for each corresponding version of a package.


#### marathon.json.mustache
This file is a [mustache template](http://mustache.github.io/) that when rendered will create a
[Marathon](http://github.com/mesosphere/marathon) app definition capable of running your service. The first level of validation is that after Mustache substitution, the result must be a JSON document. Once the JSON document is produced, it will be valid request body for Marathon's `POST /v2/apps` endpoint ([Marathon API Documentation](https://mesosphere.github.io/marathon/docs/rest-api.html)).

This is the Marathon file that we would use :

```
{
  "id": "{{service.name}}",
  "cpus": {{service.cpus}},
  "mem": {{service.mem}},
  "instances": 1,
  "container": {
    "type": "DOCKER",
    "docker": {
      "image": "{{resource.assets.container.docker.timeserverimage}}",
      "network": "HOST"
    }
  },
  "portDefinitions": [
    {
      "port": 0,
      "protocol": "tcp"
    }
  ]
}
```

The service `name`, `cpus` and `mem` are populated from the `config.json` file. The image is populated from the `resource.json` file. We are using HOST mode of networking to dynamically get a port from the available pool. Read [about Marathon ports](https://mesosphere.github.io/marathon/docs/ports.html) to understand modes in detail.


### Step 4 : Testing the package
Now that you have the package built, we need to make sure everything works as expected before publishing to the community.


#### Validation using build script.
You can execute the script inside the `scripts/build.sh` to make sure all the JSON schema comply to specifications and to install any missing libraries. This script is also executed as a precommit hook.

It may throw some error if there are any unrecognized fields in the package files. Fix those error and re-execute the command until the build is successful.

Now, we can run the Universe server locally to test and install our package.


#### Build the local Universe server
Build the Universe Server Docker image
```bash
DOCKER_IMAGE="docker-user-name/universe-server" DOCKER_TAG="time-server" docker/server/build.bash
```

This will create a Docker image `universe-server:time-server` and `docker/server/target/marathon.json` on your local machine

If you would like to publish the built Docker image, run
```bash
DOCKER_IMAGE="docker-user-name/universe-server" DOCKER_TAG="time-server" docker/server/build.bash publish
```


#### Run the local Universe server
Using the `marathon.json` that is created when building Universe Server we can run a Universe Server in our DC/OS cluster which can then be used to install packages.

Run the following commands inside the `server/target` directory to configure DC/OS to use the custom Universe Server (DC/OS 1.8+):

`dcos marathon app add marathon.json`


#### Add the Universe repo to DC/OS cluster:
Now that you have local Universe server up and running, add this to the cluster instance. You can do this from the GUI or CLI. From the `server/target` directory execute

`dcos package repo add --index=0 dev-universe http://universe.marathon.mesos:8085/repo`


#### Install the package
- You can search for you package using something like:

    `dcos package search time`
- Once you have found our `time-server` package, you can install it on to your cluster using

    `dcos package install time-server`
- Install the package and if everything works, you have successfully created a package, tested and deployed it!. You can check if your package is running at

    `dcos marathon app list`

- You can browse your endpoint by going to the cluster dashboard and clicking on Services > time-server, you will be able to see a current running task and you can click on any running task to view the endpoint url.

Now continue to next step to publish your package to the DC/OS community.


### Step 5 : Publish the package
Universe Server is a new component introduced alongside `packagingVersion` `3.0`. In order for Universe to be able to provide packages for many versions of DC/OS at the same time, it is necessary for a server to be responsible for serving the correct set of packages to a cluster based on the cluster's version.

All Pull Requests opened for Universe and the `version-3.x` branch will have their Docker image built and published to the DockerHub image [`mesosphere/universe-server`](https://hub.docker.com/r/mesosphere/universe-server/). In the artifacts tab of the build results you can find `docker/server/marathon.json` which can be used to run the Universe Server for testing in your DC/OS cluster.  For each Pull Request, click the details link of the "Universe Server Docker image" status report to view the build results.
