# Getting Started

This document is intended as a "getting started" guide. The audience are developers looking to modify or *publish* the packages to the universe. This document is written in tutorial and walk-through format. The goal is to help you "get started". It does not go into great depth on some of the conceptual or inner details. This guide aims at making a user familiar with the concepts of what a Package is and what are the roles of marathon and universe in the package life cycle.

## Prerequisites

Before the launch, make sure you have:
* Access to a running [DC/OS](https://dcos.io/docs/latest/overview/what-is-dcos/).
* [DC/OS CLI](https://dcos.io/docs/latest/cli/install/) installed and configured.
* [jq](https://stedolan.github.io/jq/download/) is installed in your environment.
* python3 in your environment.
* Docker is installed.

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

Deploying your service using the package approach makes your life easier and service management efficient. Once you have a running DC/OS cluster, you would be able to browse packages in the dashboard. By the end of this guide, you will be able to build, publish, and browse your package in the cluster.


## Create a package

Let us build a simple python http server, which, when receives a Get or a Post, responds with the current time at the server. We will start with this and build a package that provides this python server as a service.

### Step 1 : Create a simple python http server

For the purposes of this guide, we will be using python3 and the BaseHTTPServer library it has. Let's create a file called `helloworld.py` in an empty directory called `time-server`

```python
import time
import BaseHTTPServer


HOST_NAME = 'localhost' # Host name of the http server
PORT_NUMBER = 8000 # Port number of the http server

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write("<html><head><title>Time Server</title></head>")
        s.wfile.write("<body><p>The current time is %s</p>" % time.asctime())
        s.wfile.write("</body></html>")

    def do_POST(s):
        do_GET(s)

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

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run helloworld.py when the container launches
CMD ["python", "helloworld.py"]
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

`docker build -t time-server .`

Where is your built image? It’s in your machine’s local Docker image registry:

```
$ docker images

REPOSITORY         TAG                 IMAGE ID
time-server         latest              42somsoc147
```

#### Test your container

When you execute the  `docker images`, you should be able to see the your image in the displayed list. In order to make sure the image is working as expected, you can run the container by issuing the below command :

`docker run -p 80:8000 -t time-server:latest`

The `-p` option maps the host port 80 to the container port 8000. The  `-t` flag creates a pseudoTTY and since we unbuffered the python standard i/o in our Dockerfile, we will be able to see the real time logs of the server in the console. Once you executed the above command, you should be able to browse [localhost](http://localhost:80)

#### Tag and publish your container

Once you are satisfied with the functionality of your container, you can publish the docker image on to the docker registry. In our case, we execute :

`docker tag time-server docker-user-name/time-server:latest`

This tags our `time-server` image with the docker repository `time-server` in your docker user name `docker-user-name` and provide an optional tag `latest`.

Once we tag our image, we have to publish (synonmous with github push) to the docker registry so that marathon would be able to discover this in future using an url. We achieve this by executing the command :

`docker push docker-user-name/time-server:latest`

Now that we have the container ready, in the next section we will see how to create a package!

### Step 3 : Creating the package

In order to create a package, you need to have forked the [universe repo](https://github.com/mesosphere/universe) and then cloned it so that it is available in your terminal. Once you do this, go to the ./repo/package/ directory and create a folder called `time-server` under the repo/package/T/ directory (as our package name starts with T). Inside this folder, if there is already another package with a name of your choice, you have to name your package differently. We create all the required files in this package.

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

In our case, since this is the first version of our time-server, we will create the above folder structure with only one revision (with number 0) and create the required empty files. In this section, we discuss about the mandatory fields for each of the files.

#### config.json
As the name says, this file is used for any configuration purposes. As our use case is trivial and we don't have anything to configure in our time-server, we keep this file empty with minimal defaults. This is how our config.json would look like:

```
{
	"$schema": "http://json-schema.org/schema#",
	"properties": {
	}
}
```
You can read more about the various fields in this field [here](https://github.com/mesosphere/universe#configjson) or can refer to [`repo/meta/schema/config-schema.json`](repo/meta/schema/config-schema.json) for a full fledged definition.

#### resource.json
This file contains all of the externally hosted resources (E.g. Docker images, HTTP objects and
images) needed to install the application.

Below is the resource file that we use for our package. Note that we have provided our earlier published docker-user-name/time-server:latest image under the docker field here.

```
{
  "images": {
    "icon-small": "https://s3.amazonaws.com/downloads.mesosphere.io/universe/assets/icon-service-influxdb-small.png",
    "icon-medium": "https://s3.amazonaws.com/downloads.mesosphere.io/universe/assets/icon-service-influxdb-medium.png",
    "icon-large": "https://s3.amazonaws.com/downloads.mesosphere.io/universe/assets/icon-service-influxdb-large.png",
     "screenshots": [
     "https://raw.githubusercontent.com/Kentik/docker-monitor/master/screenshots/influxdb-screenshot.png"
   ]
  },
  "assets": {
    "container": {
      "docker": {
        "timeserverimage": "docker-user-name/time-server:latest"
      }
    }
  }
}
```

You can read more about the various fields in this field [here](https://github.com/mesosphere/universe#resourcejson) or can refer to [`repo/meta/schema/v3-resource-schema.json`](repo/meta/schema/v3-resource-schema.json) for a full fledged definition.

#### marathon.json.mustache


#### package.json
Every package in Universe must have a `package.json` file which specifies the high level metadata about the package.

Below is a snippet that represents our time server package.json (a version `4.0` package). This json has only the mandatory fields configured.

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
You can read more about the various fields in this field [here](https://github.com/mesosphere/universe#configjson) or can see [`repo/meta/schema/package-schema.json`](repo/meta/schema/package-schema.json) for the full json schema outlining what properties are available for each corresponding version of a package.

#### marathon.json.mustache

This file is a [mustache template](http://mustache.github.io/) that when rendered will create a
[Marathon](http://github.com/mesosphere/marathon) app definition capable of running your service. The first level of validation is that after Mustache substitution, the result must be a JSON document. Once the json document is produced, it will be valid request body for Marathon's `POST /v2/apps` endpoint ([Marathon API Documentation](https://mesosphere.github.io/marathon/docs/rest-api.html)).

This is the marathon file that we would use :


### Step 4 : Testing the package

Now that you have the package built, we need to make sure everything works as expected before publishing to the community.

#### Validation using build script.

You can execute the script inside the `scripts/build.sh` to make sure all the json schema comply to specifications and to install any missing libraries. This script is also executed as a precommit hook.

It may throw some error if there are any unrecognized fields in the package files. Fix those error and re-execute the command until the build is successful.

Now, we can run the universe server locally to test and install our package.

Build the Universe Server Docker image
```bash
DOCKER_IMAGE = "docker-user-name/universe-server" DOCKER_TAG="time-server" docker/server/build.bash
```

This will create a Docker image `universe-server:time-server` and `docker/server/target/marathon.json` on your local machine

- deploy locally (add repo to cluster)

- when done, mov eon

If you would like to publish the built Docker image, run
```bash
DOCKER_IMAGE = "docker-user-name/universe-server" DOCKER_TAG="time-server" docker/server/build.bash publish
```


### Step 5 :

Universe Server is a new component introduced alongside `packagingVersion` `3.0`. In order for Universe to be able to provide packages for many versions of DC/OS at the same time, it is necessary for a server to be responsible for serving the correct set of packages to a cluster based on the cluster's version.

All Pull Requests opened for Universe and the `version-3.x` branch will have their Docker image built and published to the DockerHub image [`mesosphere/universe-server`](https://hub.docker.com/r/mesosphere/universe-server/). In the artifacts tab of the build results you can find `docker/server/marathon.json` which can be used to run the Universe Server for testing in your DC/OS cluster.  For each Pull Request, click the details link of the "Universe Server
Docker image" status report to view the build results.


- Share package with community. PR.

- dcos package install should work anywhere.







# TODO

- Get a docker-user-name
- Get resources uploaded under downloads.mesosphere.io s3 bucket
- what are v3-resource-schema and v2-resource-schema
- Mustasche docs?
- why & who /universe
* [json-schema](TODO) is installed.
