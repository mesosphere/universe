# Getting Started
This document is intended as a "getting started" guide. The audience are developers looking to modify or *publish* the packages to the universe. This document is written in tutorial and walk-through format. The goal is to help you "get started". It does not go into great depth on some of the conceptual or inner details. This guide aims at making a user familiar with the concepts of what a Package is and what are the roles of marathon and universe in the package life cycle.


## Prerequisites
Before the launch, make sure you have met the following conditions.

### Library dependencies
* [DC/OS CLI](https://dcos.io/docs/latest/cli/install/) installed and configured.
* [jq](https://stedolan.github.io/jq/download/) is installed in your environment.
* python3 in your environment.
* Docker is installed.

### Access requirements
* Access to a running [DC/OS](https://dcos.io/docs/latest/overview/what-is-dcos/).
* The Universe Server needs to be built and run in a location accessible by the DC/OS Cluster. There is no other way to test your package otherwise.
* The marathon server needs to have access to the Docker Hub registry which has your universe server. In our guide, we use Docker Hub.

## Required nomenclature
This guide assumes you are familiar with the basics of the concepts mentioned below. Advanced user can skip this section and jump to [Create a package](#create-a-package). If you are new to DC/OS, we recommend below reading along with the external links they provide.


### What is Universe ?
The Universe is a DC/OS package repository that contains services like Spark, Cassandra, Jenkins, and many others. It allows users to install these services with a single click from the DC/OS UI or by a simple `dcos package install package_name` command from the DC/OS CLI. Many community members have already submitted their own packages to the Universe, and we encourage anyone interested to get involved with package development! It is a great way of contributing to the DC/OS ecosystem and allows users to easily get started with your favorite package.


### What is Marathon ?
[Marathon](https://mesosphere.github.io/marathon/) is a production-grade container orchestration platform for Mesosphere’s Datacenter Operating System (DC/OS) and [Apache Mesos](https://mesos.apache.org/). In order to deploy applications on top of Mesos, one can use Marathon for Mesos. Marathon is a cluster-wide init and control system for running Linux services in cgroups and Docker containers. Marathon has a number of different deploy [features](https://mesosphere.github.io/marathon/#features) and is a very mature project. Marathon runs on top of Mesos, which is a highly scalable, battle tested and flexible resource manager. Marathon is proven to scale and runs in many production environments.


### What is a package ?
There are several to deploy your service on to a running DC/OS cluster.
  * Use DCOS marathon command in CLI
  * Use Marathon REST API Directly and
  * Deploy your service as a package

Deploying your service using the package approach makes your life easier and service management efficient. Once you have a running DC/OS cluster, you would be able to browse packages in the dashboard. A package constitutes of the four required configuration files and all the external links those configuration files point to.

Package implicitly relies on marathon as the definition provided by package is converted to a marathon app template. However, marathon doesn't know about package. By the end of this guide, you will be able to build, publish, and browse your package in the cluster.


### This repository
- Current packaging version is v4 and we follow this standard for this guide. This guide will be updated as and when we release a new version.
- The packages are located in `/repo/packages` folder.
- This tutorial is in `/tutorial` folder
- You can refer to to **schema** in `/repo/meta/schema` folder. This folder has
  - config-schema.json that refers to the schema of the config.json
  - package-schema.json that refers to the schema of the package.json
  - v3-resource-schema.json that refers to the schema of the resource.json for the v3 and v4 packages
  - repo-schema.json files are not meant to be used by a developer.

## Create a package
Let us build a simple python http server, which, when receives a Get request, responds with the current time at the server. We will start with this and build a package that provides this python server as a service.


### Step 1 : Create a simple python http server
For the purposes of this guide, we will be using python3 and the BaseHTTPServer library it has. Let's create a file called `helloworld.py` in an empty directory called `time-server`

```python
import time
import BaseHTTPServer
import os


HOST_NAME = '0.0.0.0' # Host name of the http server
# Gets the port number from $PORT0 environment variable
PORT_NUMBER = int(os.environ['PORT0'])

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write("<html><head><title>Time Server</title></head>")
        s.wfile.write("<body><p>The current time is %s</p>" % time.asctime())
        s.wfile.write("</body></html>")


if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)

```

The code snippet simply starts a python server and serves the get or post requests with a html text that says the current time. You should be able to run this code snippet with `python helloworld.py` and browse [localhost:8000](http://localhost:8000).


### Step 2 : Creating a docker container
Creating a docker container is essential to distribute your service. It runs completely isolated from the host environment by default, only accessing host files and ports if configured to do so. To continue reading, you need to be familiar with docker. We recommend this [get-started](https://docs.docker.com/get-started/) guide to familiarize docker. You should have logged in to your docker account in your terminal using `docker login`.

We create a docker file (named Dockerfile) in the `time-server` directory created earlier. The Dockerfile should look like this:

```
# Use an official Python runtime as a base image
FROM python:2

# Set the working directory to /app
WORKDIR /package

# Copy the current directory contents into the container at /app
ADD . /package

# Run helloworld.py when the container launches
CMD ["python", "-u", "helloworld.py"]
```
Read through the comments to understand what each step in the Dockerfile does.


#### Build the container
That’s it! You don’t need any dependencies to be installed on your system, nor will building or running this image install them on your system.

Here’s what `ls` should show:

```
$ ls
Dockerfile		helloworld.py
```

Now run the build command. This creates a Docker image, which we’re going to tag using -t so it has a friendly name.

`docker build -t docker-user-name/time-server:part1 .`

Where is your built image? It’s in your machine’s local Docker image registry:

```
$ docker images

REPOSITORY         TAG                 IMAGE ID
time-server        part1              42somsoc147
```


#### Test your container
When you execute the  `docker images`, you should be able to see the your image in the displayed list. In order to make sure the image is working as expected, you can run the container by issuing the below command :

`docker run -p 80:8000 -t docker-user-name/time-server:part1`

The `-p` option maps the host port 80 to the container port 8000. The  `-t` flag creates a pseudoTTY and since we unbuffered the python standard i/o in our Dockerfile, we will be able to see the real time logs of the server in the console. Once you executed the above command, you should be able to browse [localhost](http://localhost:80)

*Through out the rest of this guide, we refer to `docker-user-name` as your docker user name where you access your docker images. You are expected to replace the keyword `docker-user-name` with your docker user name in all commands*

#### Change port mapping to be dynamic

If we want to get a port number dynamically from available ports, marathon provides a way to achieve this. We access the available ports using the environment variable `$PORT0`, `$PORT1`, `$PORT2` and so on. This will be explained clearly in the later section. But as of now, just change your python snippet to read the port from an environment variable as below :

```python
# Gets the port number from $PORT0 environment variable
PORT_NUMBER = int(os.environ['PORT0'])
```

Before you continue to next step, make sure to re-build your docker image.

#### Tag and publish your container
Once you are satisfied with the functionality of your container, you can publish the docker image on to the docker registry. In our case, we execute :

`docker tag time-server docker-user-name/time-server:part1`

This tags our `time-server` image with the docker repository `time-server` in your docker user name `docker-user-name` and provides an optional tag `part1`.

Once we tag our image, we have to publish (synonmous with github push) to the docker registry so that marathon would be able to discover this in future using an url. We achieve this by executing the command :

`docker push docker-user-name/time-server:part1`

Now that we have the container ready, in the next section we will see how to create a package!


### Step 3 : Creating the package
In order to create a package, you need to have forked the [universe repo](https://github.com/mesosphere/universe) and then cloned it so that it is available in your terminal. Once you do this, go to the ./repo/package/ directory and create a folder called `time-server` under the repo/package/T/ directory (as our package name starts with T). Inside this folder, if there is already another package with a name of your choice, you have to name your package differently. We create all the required files in this package.

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

In our case, since this is the first version of our time-server, we will create the above folder structure with only one revision (with number 0) and create the required empty files. As the versions of your package grow, this number increments by one unit.

***Tip : When reading the schema json files, look for `required` json field to understand what fields are mandatory***

#### config.json
As the name says, this file is used for any configuration purposes. This is how our config.json would look like:

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

We have three main properties to be configured. The `name` is the actual name of the service. The cpus and mem are the amount of CPU and Memory required for each service instance. You can read more about the various fields in this field [here](https://github.com/mesosphere/universe#configjson) or can refer to [`repo/meta/schema/config-schema.json`](repo/meta/schema/config-schema.json) for a full fledged definition.

(Note : If you need to add a config property after the merge of the PR and CI has deployed your package, you have to bump your package version and create new package. So be sure to add all the config properties that you need.)

#### resource.json
This file contains all of the externally hosted resources (E.g. Docker images, HTTP objects and
images) needed to install the application. It also contains the `cli` section that can be used to allow a package to configure native CLI subcommands for several platforms and architectures.

Below is the resource file that we use for our package. We have provided our earlier published docker-user-name/time-server:part1 image under the docker field here. Note that giving a docker image is optional and we can have other ways to execute the binary (E.g.: The package dcos-enterprise-cli doesn't use a docker image to install the binary.)

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

You can put the icons related to your package and screenshots of your service if needed here. You can read more about the various fields in this field [here](https://github.com/mesosphere/universe#resourcejson) or can refer to [`repo/meta/schema/v3-resource-schema.json`](repo/meta/schema/v3-resource-schema.json) for a full fledged definition.


#### package.json
Every package in Universe must have a `package.json` file which specifies the high level metadata about the package.

Below is a snippet that represents our time server package.json (a version `4.0` package). This json has only the mandatory fields configured. As this is our first version, we fill the version field to be 1.0.0

```
{
  "packagingVersion": "4.0",
  "name": "time-server",
  "version": "1.0.0",
  "maintainer": "https://github.com/mesosphere/universe",
  "description": "This is a simple python http server that displays a webpage that says the current time at the server location",
  "tags": ["python", "http", "time-server"]
}
```

Note that the version field specifies the version of the package and this is independent of the folder number inside the `time-server` folder.

You can read more about the various fields in this field [here](https://github.com/mesosphere/universe#configjson) or can see [`repo/meta/schema/package-schema.json`](repo/meta/schema/package-schema.json) for the full json schema outlining what properties are available for each corresponding version of a package.


#### marathon.json.mustache
This file is a [mustache template](http://mustache.github.io/) that when rendered will create a
[Marathon](http://github.com/mesosphere/marathon) app definition capable of running your service. The first level of validation is that after Mustache substitution, the result must be a JSON document. Once the json document is produced, it will be valid request body for Marathon's `POST /v2/apps` endpoint ([Marathon API Documentation](https://mesosphere.github.io/marathon/docs/rest-api.html)).

This is the marathon file that we would use :

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

The service id, cpus and mem are populated from the config json file. The image is populated from the resource.json file. We are using HOST mode of networking to dynamically get a port from the available pool. Read [about marathon ports](https://mesosphere.github.io/marathon/docs/ports.html) to understand modes in detail.


### Step 4 : Testing the package
Now that you have the package built, we need to make sure everything works as expected before publishing to the community.


#### Validation using build script.
You can execute the script inside the `scripts/build.sh` to make sure all the json schema comply to specifications and to install any missing libraries. This script is also executed as a precommit hook.

It may throw some error if there are any unrecognized fields in the package files. Fix those error and re-execute the command until the build is successful.

Now, we can run the universe server locally to test and install our package.


#### Build the local universe server
Build the Universe Server Docker image
```bash
DOCKER_IMAGE="docker-user-name/universe-server" DOCKER_TAG="time-server" docker/server/build.bash
```

This will create a Docker image `universe-server:time-server` and `docker/server/target/marathon.json` on your local machine

If you would like to publish the built Docker image, run
```bash
DOCKER_IMAGE="docker-user-name/universe-server" DOCKER_TAG="time-server" docker/server/build.bash publish
```


#### Run the local universe server
Using the `marathon.json` that is created when building Universe Server we can run a Universe Server in our DC/OS cluster which can then be used to install packages.

Run the following commands inside the `server/target` directory to configure DC/OS to use the custom Universe Server (DC/OS 1.8+):

`dcos marathon app add marathon.json`


#### Add the universe repo to DC/OS cluster:
Now that you have local universe server up and running, add this to the cluster instance. You can do this from the GUI or CLI. From the `server/target` directory execute

`dcos package repo add --index=0 dev-universe http://universe.marathon.mesos:8085/repo`


#### Install the package
- You can search for you package using something like:

    `dcos package search time`
- Once you have found our `timeserver` package, you can install it on to your cluster using

    `dcos package install timeserver`
- Install the package and if everything works, you have successfully created a package, tested and deployed it!. You can check if your package is running at

    `dcos marathon app list`

- You can browse your endpoint by going to the cluster dashboard and clicking on Services > time-server, you will be able to see a current running task and you can click on any running task to view the endpoint url.

Now continue to next step to publish your package to the DC/OS community.


### Step 5 : Publish the package
Universe Server is a new component introduced alongside `packagingVersion` `3.0`. In order for Universe to be able to provide packages for many versions of DC/OS at the same time, it is necessary for a server to be responsible for serving the correct set of packages to a cluster based on the cluster's version.

All Pull Requests opened for Universe and the `version-3.x` branch will have their Docker image built and published to the DockerHub image [`mesosphere/universe-server`](https://hub.docker.com/r/mesosphere/universe-server/). In the artifacts tab of the build results you can find `docker/server/marathon.json` which can be used to run the Universe Server for testing in your DC/OS cluster.  For each Pull Request, click the details link of the "Universe Server Docker image" status report to view the build results.
