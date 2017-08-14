# Get Started Creating a DC/OS Package
This tutorials provides a walkthrough of creating a Universe package. The audience is developers who want to modify or *publish* packages to the Universe. This tutorial will familiarize you with package concepts and the roles of Marathon and Universe in the package life cycle. It does not go into great depth on some of the conceptual or inner details. This guide aims at making a user familiar with the concepts of what a Package is and what are the roles of Marathon and Universe in the package life cycle.

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
	- [Step 1 : Create a simple Python HTTP Server](#step-1--create-a-simple-python-http-server)
		- [Change port mapping to be dynamic](#change-port-mapping-to-be-dynamic)
	- [Step 2 : Creating a Docker container](#step-2--creating-a-docker-container)
		- [Build the container](#build-the-container)
		- [Test your container](#test-your-container)
		- [Tag and publish your container](#tag-and-publish-your-container)
	- [Step 3 : Creating a DC/OS Package](#step-3--creating-a-dcos-package)
		- [config.json](#configjson)
		- [resource.json](#resourcejson)
		- [package.json](#packagejson)
		- [marathon.json.mustache](#marathonjsonmustache)
	- [Step 3.1 : DC/OS Integration](#step-31--dcos-integration)
		- [Service Endpoints](#service-endpoints)
		- [Health Checks](#health-checks)
	- [Step 4 : Testing the package](#step-4--testing-the-package)
		- [Validation using build script.](#validation-using-build-script)
		- [Build the Universe server](#build-the-universe-server)
		- [Run the local Universe server](#run-the-local-universe-server)
		- [Add the Universe repo to DC/OS cluster:](#add-the-universe-repo-to-dcos-cluster)
		- [Install the package](#install-the-package)
		- [Test the package](#test-the-package)
	- [Step 5 : Publish the package](#step-5--publish-the-package)

## Required Terminology

### What is Universe?
The Universe is a DC/OS package repository that contains services like Spark, Cassandra, Jenkins, and many others. It allows users to install these services with a single click from the DC/OS UI or by a simple `dcos package install <package_name>` command from the DC/OS CLI. Many community members have already submitted their own packages to the Universe, and anyone interested is encouraged to get involved with package development! Submitting a package is a great way to contribute to the DC/OS ecosystem and allows users to easily get started with your favorite package.


### What is Marathon?
You can use Marathon to deploy applications to DC/OS. [Marathon](https://mesosphere.github.io/marathon/) is a production-grade container orchestration platform for Mesosphere’s Datacenter Operating System (DC/OS) and [Apache Mesos](https://mesos.apache.org/). In order to deploy applications on top of Mesos, one can use Marathon for Mesos. Marathon is a cluster-wide init and control system for running Linux services in cgroups and Docker containers. Marathon has a number of different deploy [features](https://mesosphere.github.io/marathon/#features) and is a very mature project. Marathon runs on top of Mesos, which is one of the core components of DC/OS that predates DC/OS itself, bringing maturity and stability to the platform. Marathon is proven to scale and runs in many production environments.


### What is a package?
There are several ways to deploy your service onto a running DC/OS cluster.
  * Use the DC/OS Marathon command in the CLI.
  * Use the Marathon REST API directly.
  * Deploy your service as a package.

Deploying your service using the package approach makes your life easier and service management efficient. After you have a running DC/OS, you can browse packages in the GUI [dashboard](https://docs.mesosphere.com/latest/gui/#universe). A package consists of the four required configuration files (`config.json`, `package.json`, `resource.json`, and `marathon.json.mustache`) and all of the external files linked from them.

A package implicitly relies on Marathon; its contents are used to generate a Marathon app definition. By the end of this guide, you will be able to build, publish, and browse your package in the cluster.


## Prerequisites
Before starting this guide, make sure you have the following prerequisites.

### Library dependencies
* [DC/OS CLI](https://dcos.io/docs/latest/cli/install/) installed and configured.
* [jq](https://stedolan.github.io/jq/download/) is installed in your environment.
* `python3` in your environment.
* Docker is installed.

### Access requirements
* Access to a running [DC/OS](https://dcos.io/install/).
* Mesos needs access to the Docker registry that has your Universe Server. In this guide, Docker Hub is used as the Docker registry.


### This repository
- This guide uses the packaging version v4. This guide will be updated as and when a new version is released.
- The packages are located in `repo/packages` directory.
- This tutorial is in `docs/tutorial` directory
- You can refer to **schemas** in `repo/meta/schema` directory. This directory has
  - `config-schema.json` that refers to the schema of the `config.json`
  - `package-schema.json` that refers to the schema of the `package.json`
  - `v3-resource-schema.json` that refers to the schema of the `resource.json` for the v3 and v4 packages
  - `*-repo-schema.json` files are not meant to be used by package developers; they instead define the schema for the API between Universe and DC/OS.

## Create a package
In this step, you build a package that provides a Python server as a DC/OS service. The Python server receives an HTTP GET request and responds with the current time at the server.

### Step 1 : Create a simple Python HTTP Server
For the purposes of this guide, Python 3 the HTTPServer module provided by its standard library is used. Create a file called `helloworld.py` in an empty directory called `time-server-service`.

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

If you want to get a port number dynamically from available ports, Marathon provides a way to achieve this. You can access the available ports using the environment variable `$PORT0`, `$PORT1`, `$PORT2` and so on. This will be explained clearly in a later section. But for now, just change your Python snippet to read the port from an environment variable as below :

```python
# Gets the port number from $PORT0 environment variable
PORT_NUMBER = int(os.environ['PORT0'])
```

Once you do this, you can browse your server after executing `PORT0=8000 python3 helloworld.py`

### Step 2 : Creating a Docker container
Creating a Docker container is essential to distribute _this_ service. It runs completely isolated from the host environment by default, only accessing host files and ports if configured to do so. To continue reading, you need to be familiar with Docker; this [get-started](https://docs.docker.com/get-started/) guide is recommended. You should have logged in to your Docker account in your terminal using `docker login`.

_Note: Giving a Docker image is optional and you can have other ways to execute the binary (E.g.: The package `cassandra` doesn't use a Docker image to install the binary.)._

Create a Docker file (named `Dockerfile`) in the `time-server-service` directory created earlier. The `Dockerfile` should look like this:

```bash
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

*Throughout the rest of this guide, refer to `docker-user-name` as your Docker user name where you access your Docker images from a registry such as Docker Hub. You are expected to replace the keyword `docker-user-name` with your Docker user name in all commands and files*

Now that you have everything ready, you can build the container. Here’s what `ls` should show:
```
$ ls
Dockerfile		helloworld.py
```
Now run the build command. This creates a Docker image which you are going to tag using `-t` so it has a friendly name.

`docker build -t docker-user-name/time-server:part1 .`

Where is your built image? It's in your machine's local Docker daemon:

```
$ docker images

REPOSITORY                        TAG         IMAGE ID
docker-user-name/time-server      part1       42somsoc147
```


#### Test your container
When you execute `docker images`, you should be able to see the your image in the displayed list. To make sure the image is working as expected, you can run the container by executing the command below :

`docker run --env PORT0=8000 -p 80:8000 -t docker-user-name/time-server:part1`

**Note**: You must set the value of `PORT0` explicitly because Marathon sets this value when it launches the container, which has not happened yet.

The `-p` option maps the host port 80 to the container port 8000. The  `-t` flag creates a pseudoTTY and since you unbuffered the Python standard I/O in your `Dockerfile`, you will be able to see the real time logs of the server in the console. Once you have executed the above command, you should be able to browse [localhost](http://localhost:80). You can test the url with `curl localhost:8000` and your server should return the current time.


#### Tag and publish your container
Once you are satisfied with the functionality of your container, you can publish the Docker image on to the Docker registry. In this case, you can execute :

`docker tag time-server docker-user-name/time-server:part1`

This tags your `time-server` image with the Docker repository `time-server` in your Docker user name `docker-user-name` and provides an optional tag `part1`.

Once you tag your image, you have to publish (synonmous with `git push`) to the Docker registry so that Marathon will be able to discover this in the future using an URL. You can achieve this by executing the command :

`docker push docker-user-name/time-server:part1`

Now that you have the container ready, in the next section you will see how to create a package!

### Step 3 : Creating a DC/OS Package
In order to create a package, you need to have forked the [Universe repo](https://github.com/mesosphere/universe) and then cloned it so that it is available in your terminal. Once you do this, create a directory named `time-server` under the `repo/package/T` directory (as your package name starts with the letter "t"). Inside this directory, if there is already another package with a name of your choice, you have to name your package differently. You create all the required files in this package.

Each package has its own directory, with one subdirectory for each package revision. Each package revision directory contains the set of files necessary to create a consumable package that can be used by a DC/OS Cluster to install the package. For example, your package will look like this:

```
└── repo/package/T/time-server
    ├── 0
    │   ├── config.json
    │   ├── resource.json
    │   ├── marathon.json.mustache
    │   └── package.json
    └── ...
```

In this guide, since this is the first version of the time-server, you will create the above directory structure with only one revision (with number 0) and create the required empty files. As the versions of your package grow, this number increments by one unit. Also, once package revision has been committed to Universe, it files should never be modified. A new revision must be created for any change.

***Tip : When reading the schema JSON files, look for `required` JSON field to understand what fields are mandatory***

#### config.json
As the name says, this file specifies how your package can be configured. This is how your `config.json` should look:

```json
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

In this example, there are three main properties to be configured. The `name` is the actual name of the service running in DC/OS. The `cpus` and `mem` are the amount of CPU and Memory required for each service instance. You can read more about the various fields in this file [here](https://github.com/mesosphere/universe#configjson) or can refer to [`repo/meta/schema/config-schema.json`](/repo/meta/schema/config-schema.json) for a full fledged definition.

(Note : If you need to add a config property after your package revision has been committed to Universe, you have to bump your package version and create new package. So be sure to add all the config properties that you need.)

#### resource.json
This file contains all of the externally hosted resources (e.g. Docker images, HTTP objects and images) needed to install the application. It also contains the `cli` section that can be used to allow a package to configure native CLI subcommands for several platforms and architectures.

Below is the resource file that you use for the `time-server` package. You can provide the earlier published `docker-user-name/time-server:part1` image under the `docker` JSON field here. Note that giving a Docker image is optional and you can have other ways to execute the binary. As mentioned earlier, The package `cassandra` doesn't use a Docker image to install the binary; instead, it tells Marathon to run a shell command. It has all the dependencies it needs because they are specified as URIs in `resource.json`

```json
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

You can put the icons related to your package and screenshots of your service if needed here. You can read more about the various fields in this file [here](https://github.com/mesosphere/universe#resourcejson) or can refer to [`repo/meta/schema/v3-resource-schema.json`](/repo/meta/schema/v3-resource-schema.json) for a full fledged definition.


#### package.json
Every package in Universe must have a `package.json` file which specifies the high level metadata about the package.

Below is a snippet that represents your time server `package.json` (a version `4.0` package). This JSON has only the mandatory fields configured. As this is your initial version, you can fill the version field to be `0.1.0`

```json
{
  "packagingVersion": "4.0",
  "name": "time-server",
  "version": "0.1.0",
  "maintainer": "https://github.com/mesosphere/universe",
  "description": "This is a simple Python HTTP server that displays a webpage that says the current time at the server location",
  "tags": ["python", "http", "time-server"]
}
```

Note that the version field specifies a human-readable version of the package and this is independent of the directory number inside the `time-server` directory.

You can read more about the various fields in this file [here](https://github.com/mesosphere/universe#configjson) or can see [`repo/meta/schema/package-schema.json`](/repo/meta/schema/package-schema.json) for the full JSON schema outlining what properties are available for each corresponding version of a package.


#### marathon.json.mustache
This file is a [mustache template](http://mustache.github.io/) that when rendered will create a
[Marathon](http://github.com/mesosphere/marathon) app definition capable of running your service. The first level of validation is that after Mustache substitution, the result must be a JSON document. Once the JSON document is produced, it must be a valid request body for Marathon's `POST /v2/apps` endpoint ([Marathon API Documentation](https://mesosphere.github.io/marathon/docs/rest-api.html)).

This is how the Marathon file should look like:

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

The service `name`, `cpus` and `mem` are populated from the default values in the `config.json` file. The image is populated from the `resource.json` file. Here, `HOST` mode of networking is used to dynamically get a port from the available pool. Read [about Marathon ports](https://mesosphere.github.io/marathon/docs/ports.html) to understand modes in detail.

If you need further examples, you can refer to the [repo/packages/H/hello-world](/repo/packages/H/hello-world) package.

### Step 3.1 : DC/OS Integration

By default, a DC/OS service is deployed on a [private agent node](https://dcos.io/docs/1.9/overview/concepts/#private-agent-node). To allow a user to control configuration or monitor a service, use the admin router as a reverse proxy. Admin router can proxy calls on the master node to a service on a private node.

The Admin Router currently supports only one reverse proxy destination. This step is optional. If you don't want to expose your service endpoint, you can skip to the next step.

#### Service Endpoints

The Admin Router allows Marathon tasks to define custom service UI and HTTP endpoints, which are made available as `/service/<service-name>`. Set the following Marathon task labels to enable this:

```json
"labels": {
    "DCOS_SERVICE_NAME": "<service-name>",
    "DCOS_SERVICE_PORT_INDEX": "0",
    "DCOS_SERVICE_SCHEME": "http"
  }
```

To enable the forwarding to work reliably across task failures, we recommend co-locating the endpoints with the task. This way, if the task is restarted on another host and with different ports, Admin Router will pick up the new labels and update the routing. **Note**: Due to caching, there can be an up to 30-second delay before the new routing is working.

We recommend having only a single task setting these labels for a given service name. If multiple task instances have the same service name label, Admin Router will pick one of the task instances deterministically, but this might make debugging issues more difficult.

Since the paths to resources for clients connecting to Admin Router will differ from those paths the service actually has, ensure the service is configured to run behind a proxy. This often means relative paths are preferred to absolute paths. In particular, resources expected to be used by a UI should be verified to work through a proxy.

Tasks running in nested [Marathon app groups](https://mesosphere.github.io/marathon/docs/application-groups.html) will be available only using their service name (i.e., `/service/<service-name>`), not by the Marathon app group name (i.e., `/service/app-group/<service-name>`).


#### Health Checks

Service health check information can be surfaced in the DC/OS services UI tab by defining one or more `healthChecks` in the Service’s Marathon template. For example:

```
"healthChecks": [
   {
       "path": "/",
       "portIndex": 0,
       "protocol": "HTTP",
       "gracePeriodSeconds": 5,
       "intervalSeconds": 60,
       "timeoutSeconds": 10,
       "maxConsecutiveFailures": 3
   }
]
```

See the [health checks documentation](https://mesosphere.github.io/marathon/docs/health-checks.html) for more information.

In this guide, the `time-server` is not a Mesos framework. If your service is a framework and you want the tasks to show up in the UI, then you need to set the label `DCOS_PACKAGE_FRAMEWORK_NAME` to the name of the framework.

```json
"labels": {
  "DCOS_PACKAGE_FRAMEWORK_NAME": "time-server"
}
 ```

 In order to expose the `time-server` service as an endpoint and add health checks to it, add the above-mentioned labels. Your new `marathon.json.mustache` should look like this :

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
   ],
   "labels": {
     "DCOS_SERVICE_NAME": "{{service.name}}",
     "DCOS_SERVICE_PORT_INDEX": "0",
     "DCOS_SERVICE_SCHEME": "http"
   },
   "healthChecks": [
     {
       "path": "/",
       "portIndex": 0,
       "protocol": "HTTP",
       "gracePeriodSeconds": 5,
       "intervalSeconds": 60,
       "timeoutSeconds": 10,
       "maxConsecutiveFailures": 3
     }
   ]
 }
 ```


### Step 4 : Testing the package

Now that the package is built, you need to make sure everything works as expected before publishing to the community.


#### Validation using build script

You can execute the script inside the `scripts/build.sh` to make sure all the JSON schema conform to their respective schemas and to install any missing libraries. This script is also executed as a precommit hook.

It may throw some errors if there are any unrecognized fields in the package files. Fix those errors and re-execute the command until the build is successful.

Now, you can build the Universe server locally, and run in the DC/OS cluster to test and install your package.

Universe Server is a new component introduced alongside `packagingVersion` `3.0`. In order for Universe to be able to provide packages for many versions of DC/OS at the same time, it is necessary for a server to be responsible for serving the correct set of packages to a cluster based on the cluster's version.


#### Build the Universe server

Build the Universe Server Docker image:
```bash
DOCKER_IMAGE="docker-user-name/universe-server" DOCKER_TAG="time-server" docker/server/build.bash
```

This will create a Docker image `universe-server:time-server` and `docker/server/target/marathon.json` on your local machine.

If you would like to publish the built Docker image to Docker Hub, run:
```bash
DOCKER_IMAGE="docker-user-name/universe-server" DOCKER_TAG="time-server" docker/server/build.bash publish
```


#### Run the local Universe server
Using the `marathon.json` that is created when building Universe Server, you can run a Universe Server in the DC/OS cluster which can then be used to install packages.

Run the following commands inside the `server/target` directory to configure DC/OS to use the custom Universe Server (DC/OS 1.8+):

`dcos marathon app add marathon.json`


#### Add the Universe repo to DC/OS cluster:
Now that you have local Universe Server up and running, add it to the cluster's package manager as a repository. You can do this from the GUI or CLI. To achieve this from CLI, execute:

`dcos package repo add --index=0 dev-universe http://universe.marathon.mesos:8085/repo`


#### Install the package
- You can search for your package using something like:

    `dcos package search time`
- Once you have found your `time-server` package, you can install it onto your cluster using

    `dcos package install time-server`
- Install the package and if everything works, you have successfully created a package, tested and deployed it! You can check if your package is running at

    `dcos package list`

- You can browse your endpoint by going to the cluster dashboard and clicking on Services > time-server, you will be able to see a current running task and you can click on any running task to view the endpoint URL.


#### Test the package

If you have followed the earlier instructions in configuring a [service endpoint](#service-endpoints), then you can test the url with `curl` command using:

    `curl https://<DC/OS-Cluster>/service/time-server`

or just open up the url in your favorite browser and you should be able to see the current time.


Now continue to the next step to publish your package to the DC/OS community.


### Step 5 : Publish the package
To add a package into the Universe, you will need to create a Pull Request against the `mesosphere/universe` repo, `version-3.x` branch. Once you have raised a PR, the CI(Continuous Integration) kicks in and runs automated tests to make sure everything works together. Once the CI passes all the automated tests, mesosphere reviews the PR and merges them once they are ready and your package will be ready to :rocket:.

All Pull Requests opened for Universe and the `version-3.x` branch will have their Universe Server Docker image built and published to the DockerHub image [`mesosphere/universe-server`](https://hub.docker.com/r/mesosphere/universe-server/). In the artifacts tab of the build results you can find `docker/server/marathon.json` which can be used to run the Universe Server for testing in your DC/OS cluster.  For each Pull Request, click the details link of the "Universe Server Docker image" status report to view the build results.
