# Mesosphere Universe

| Build | Status |
|---|---|
|CI   | [![Build Status](https://teamcity.mesosphere.io/guestAuth/app/rest/builds/buildType:(id:Oss_Universe_Ci)/statusIcon)](https://teamcity.mesosphere.io/viewType.html?buildTypeId=Oss_Universe_Ci&guest=1)|
| Universe Server | [![Build Status](https://teamcity.mesosphere.io/guestAuth/app/rest/builds/buildType:(id:Oss_Universe_UniverseServer)/statusIcon)](https://teamcity.mesosphere.io/viewType.html?buildTypeId=Oss_Universe_UniverseServer&guest=1)|

Mesosphere Universe registry of packages made available for DC/OS Clusters.

#### Table of Contents
* [Universe Purpose](#universe-purpose)
  * [Library Dependencies](#library-dependencies)
* [Publish a Package](#publish-a-package-1)
  * [Creating a Package](#creating-a-package)
    * [`package.json`](#packagejson)
      * [`.minDcosReleaseVersion`](#mindcosreleaseversion)
    * [`config.json`](#configjson)
    * [`marathon.json.mustache`](#marathonjsonmustache)
    * [`command.json`](#commandjson)
    * [`resource.json`](#resourcejson)
      * [Docker Images](#docker-images)
      * [Images](#images)
      * [CLI Resources](#cli-resources)
  * [Submit your Package](#submit-your-package)
* [Repository Consumption](#repository-consumption-1)
  * [Universe Server](#universe-server)
    * [Build Universe Server locally](#build-universe-server-locally)
    * [Run Universe Server](#run-universe-server)
  * [Consumption Protocol](#consumption-protocol)
  * [Supported DC/OS Versions](#supported-dcos-versions)


## Universe Purpose
You can publish and store packages in the Universe repository. The packages can then be consumed by DC/OS. This git repo facilitates these three necessary functions - to publish, store and consume packages. You can publish and store packages in the Universe repository. The packages can then be consumed by DC/OS. If you are new to Universe and Packages, this [Get Started Guide](docs/tutorial/GetStarted.md) is highly recommended.

### Library dependencies
* [jq](https://stedolan.github.io/jq/download/) is installed in your environment.
* `python3` is installed in your environment.
* Docker is installed in your environment.

### Publish a Package

To publish a package to Universe, fork this repo and open a Pull Request. A set of automated builds will be run against
the Pull Request to ensure the modifications made in the PR leave the Universe well formed.
See [Creating a Package](#creating-a-package) for details.

### Registry of Packages

The registry of published packages is maintained as the contents of this repo in the `repo/packages` directory. As of
repository version `3.0` multiple packaging versions are allowed to co-exist in the same repository. Validation of
packages are coordinated based on the packaging version defined in `package.json`.

### Repository Consumption

In order for published packages to be consumed and installed in a DC/OS Cluster the Universe Server needs to be built
and run in a location accessible by the DC/OS Cluster. See [Universe Server](#universe-server) for details on
building the Universe artifacts and Server.

## Publish a Package

### Creating a Package

Each package has its own directory, with one subdirectory for each package revision. Each package revision directory
contains the set of files necessary to create a consumable package that can be used by a DC/OS Cluster to install
the package.
```
└── repo/package/F/foo
    ├── 0
    │   ├── command.json
    │   ├── config.json
    │   ├── marathon.json.mustache
    │   ├── resource.json
    │   └── package.json
    ├── 1
    │   ├── command.json
    │   ├── config.json
    │   ├── marathon.json.mustache
    │   ├── resource.json
    │   └── package.json
    └── ...
```


#### `package.json`

|Packaging Version|   |
|-----------------|---|
|2.0|required|
|3.0|required|
|4.0|required|

Every package in Universe must have a `package.json` file which specifies the high level metadata about the package.

Currently, a package can specify one of three values for `.packagingVersion`
either `2.0` or `3.0` or `4.0`; which version is declared
will dictate which other files are required for the complete package as well as the schema(s) all the files must
adhere to. Below is a snippet that represents a version `4.0` package.

See [`repo/meta/schema/package-schema.json`](repo/meta/schema/package-schema.json) for the full json schema outlining
what properties are available for each corresponding version of a package.

```json
{
  "packagingVersion": "4.0",
  "name": "foo",
  "version": "1.2.3",
  "tags": ["mesosphere", "framework"],
  "maintainer": "help@bar.io",
  "description": "Does baz.",
  "scm": "https://github.com/bar/foo.git",
  "website": "http://bar.io/foo",
  "framework": true,
  "upgradesFrom": ["1.2.2"],
  "downgradesTo": ["1.2.2"],
  "minDcosReleaseVersion": "1.10",
  "postInstallNotes": "Have fun foo-ing and baz-ing!"
}
```

For the first version of the package, add this line to the beginning of `preInstallNotes`: ```This DC/OS Service is currently in preview. There may be bugs, incomplete features, incorrect documentation, or other discrepancies. Preview packages should never be used in production!``` It will be removed once the package has been tested and used by the community.

###### `.minDcosReleaseVersion`

|Packaging Version|   |
|-----------------|---|
|2.0|not supported|
|3.0|optional|
|4.0|optional|

Introduced in `packagingVersion` `3.0`, `.minDcosReleaseVersion` can be specified as a property of `package.json`.
When `.minDcosReleaseVersion` is specified the package will only be made available to DC/OS clusters with a DC/OS
Release Version greater than or equal to (`>=`) the value specified.

For example, `"minDcosReleaseVersion" : "1.8"` will prevent the package from being installed on clusters older than DC/OS 1.8.

###### `.upgradesFrom`

|Packaging Version|   |
|-----------------|---|
|2.0|not supported|
|3.0|not supported|
|4.0|optional|

Introduced in `packagingVersion` `4.0`, `.upgradesFrom` can be specified as a property of `package.json`.
When `.upgradesFrom` is specified this indicates to users that the package is able to upgrade from any of
the versions listed in the property. It is the resposibility of the package creator to make sure that this
is indeed the case.

###### `.downgradesTo`

|Packaging Version|   |
|-----------------|---|
|2.0|not supported|
|3.0|not supported|
|4.0|optional|

Introduced in `packagingVersion` `4.0`, `.downgradesTo` can be specified as a property of `package.json`.
When `.downgradesTo` is specified this indicates to users that the package is able to downgrade to any of
the versions listed in the property. It is the resposibility of the package creator to make sure that this
is indeed the case.

#### `config.json`

|Packaging Version|   |
|-----------------|---|
|2.0|optional|
|3.0|optional|
|4.0|optional|

This file describes the configuration properties supported by the package, represented as a
[json-schema](http://spacetelescope.github.io/understanding-json-schema/). Each property can specify whether or not it
is required, a default value, as well as some basic validation.

Users can then [override specific values](https://docs.mesosphere.com/1.7/usage/services/config/) at
installation time by passing an options file to the DC/OS CLI or by setting config values through the
DC/OS UI (since DC/OS 1.7).

```json
{
  "type": "object",
  "properties": {
    "foo": {
      "type": "object",
      "properties": {
        "baz": {
          "type": "integer",
          "description": "How many times to do baz.",
          "minimum": 0,
          "maximum": 16,
          "required": false,
          "default": 4
        }
      },
      "required": ["baz"]
    }
  },
  "required": ["foo"]
}
```


#### `marathon.json.mustache`

|Packaging Version|   |
|-----------------|---|
|2.0|required|
|3.0|optional|
|4.0|optional|

This file is a [mustache template](http://mustache.github.io/) that when rendered will create a
[Marathon](http://github.com/mesosphere/marathon) app definition capable of running your service.

Variables in the mustache template will be evaluated from a union object created by merging three objects in the
following order:

1. Defaults specified in `config.json`

2. User supplied options from either the DC/OS CLI or the DC/OS UI

3. The contents of `resource.json`

```json
{
  "id": "foo",
  "cpus": 1.0,
  "mem": 1024,
  "instances": 1,
  "args": ["{{{foo.baz}}}"],
  "container": {
    "type": "DOCKER",
    "docker": {
      "image": "{{resource.assets.container.docker.foo23b1cfe8e04a}}",
      "network": "BRIDGE",
      "portMappings": [
        {
          "containerPort": 8080,
          "hostPort": 0,
          "servicePort": 0,
          "protocol": "tcp"
        }
      ]
    }
  }
}
```

See the
[Marathon API Documentation](https://mesosphere.github.io/marathon/docs/rest-api.html)
for more detailed instruction on app definitions.

#### `command.json`

|Packaging Version|   |
|-----------------|---|
|2.0|optional|
|3.0|optional **[Deprecated]**|
|4.0|not supported|

As of `packagingVersion` `3.0`, `command.json` is deprecated in favor of the `.cli` property of `resource.json`.
See [CLI Resources](#cli-resources) for details.

Describes how to install the package's CLI via pip, the Python package manager. This document represents the
format of a Pip requirements file where each element in the array is a line in the requirements file.

```json
{
  "pip": [
    "https://pypi.python.org/packages/source/f/foo/foo-1.2.3.tar.gz"
  ]
}
```

Packaging version 4.0 does not support command.json. The presence of command.json in the
directory will fail the universe validation.

#### `resource.json`

|Packaging Version|   |
|-----------------|---|
|2.0|optional|
|3.0|optional|
|4.0|optional|

This file contains all of the externally hosted resources (E.g. Docker images, HTTP objects and
images) needed to install the application.

See [`repo/meta/schema/v2-resource-schema.json`](repo/meta/schema/v2-resource-schema.json) and
[`repo/meta/schema/v3-resource-schema.json`](repo/meta/schema/v3-resource-schema.json) for the full
json schema outlining what properties are available for each corresponding version of a package.

```json
{
  "images": {
    "icon-small": "http://some.org/foo/small.png",
    "icon-medium": "http://some.org/foo/medium.png",
    "icon-large": "http://some.org/foo/large.png",
    "screenshots": [
      "http://some.org/foo/screen-1.png",
      "http://some.org/foo/screen-2.png"
    ]
  },
  "assets": {
    "uris": {
      "log4j-properties": "http://some.org/foo/log4j.properties"
    },
    "container": {
      "docker": {
        "23b1cfe8e04a": "some-org/foo:1.0.0"
      }
    }
  }
}
```

##### Docker Images

For the Docker image, please use the image ID for the referenced image. You can find this by
pulling the image locally and running `docker images some-org/foo:1.0.0`.

##### Images

While `images` is an optional field, it is highly recommended you include icons and screenshots
in `resource.json` and update the path definitions accordingly. Specifications are as follows:

* `icon-small`: 48px (w) x 48px (h)
* `icon-medium`: 96px (w) x 96px (h)
* `icon-large`: 256px (w) x 256px (h)
* `screenshots[...]`: 1200px (w) x 675px (h)

**NOTE:** To ensure your service icons look beautiful on retina-ready displays,
please supply 2x versions of all icons. No changes are needed to
`resource.json` - simply supply an additional icon file with the text `@2x` in
the name before the file extension.
For example, the icon `icon-cassandra-small.png` would have a retina-ready
alternate image named `icon-cassandra-small@2x.png`.

##### CLI Resources

|Packaging Version|   |
|-----------------|---|
|2.0|not supported|
|3.0|optional|
|4.0|optional|

The new `.cli` property allows for a package to configure native CLI subcommands for several platforms and
architectures.

```json
{
  "cli":{
    "binaries":{
      "darwin":{
        "x86-64":{
          "contentHash":[
            { "algo": "sha256", "value": "..." }
          ],
          "kind": "executable",
          "url":"https://some.org/foo/1.0.0/cli/darwin/dcos-foo"
        }
      },
      "linux":{
        "x86-64":{
          "contentHash":[
            { "algo":"sha256", "value":"..." }
          ],
          "kind":"executable",
          "url":"https://some.org/foo/1.0.0/cli/linux/dcos-foo"
        }
      },
      "windows":{
        "x86-64":{
          "contentHash":[
            { "algo":"sha256", "value":"..." }
          ],
          "kind":"executable",
          "url":"https://some.org/foo/1.0.0/cli/windows/dcos-foo"
        }
      }
    }
  }
}
```

### Submit your Package

Developers are invited to publish a package containing their DC/OS Service by submitting a Pull Request targeted at
the `version-3.x` branch of this repo.

Full Instructions:

1. Fork this repo and clone the fork:

  ```bash
  git clone https://github.com/<user>/universe.git /path/to/universe
  ```

2. Run the verification and build script:

  ```bash
  scripts/build.sh
  ```

3. Verify all build steps completed successfully
4. Submit a pull request against the `version-3.x` branch with your changes. Every pull request opened will have a set
   of automated verifications run against it. These automated verification are reported against the pull request using
   the GitHub status API. All verifications must pass in order for a pull request to be eligible for merge.

5. Respond to manual review feedback provided by the DC/OS Community.
  * Each Pull Request to Universe will also be manually reviewed by a member of the DC/OS Community. To ensure your
    package is able to be made available to users as quickly as possible be sure to respond to the feedback provided.
6. Add a getting started example of how to install and use the DC/OS package. To add the example, fork the [`examples`](https://github.com/dcos/examples) repo and send in a pull request. Re-use the format from the existing examples there.


## Repository Consumption

In order for Universe to be consumed by DC/OS the build process needs to be run to create the Universe Server.

### Universe Server

Universe Server is a new component introduce alongside `packagingVersion` `3.0`. In order for Universe to be able to
provide packages for many versions of DC/OS at the same time, it is necessary for a server to be responsible for serving
the correct set of packages to a cluster based on the cluster's version.

All Pull Requests opened for Universe and the `version-3.x` branch will have their Docker image built and published
to the DockerHub image [`mesosphere/universe-server`](https://hub.docker.com/r/mesosphere/universe-server/).
In the artifacts tab of the build results you can find `docker/server/marathon.json` which can be used to run the
Universe Server for testing in your DC/OS cluster.  For each Pull Request, click the details link of the "Universe Server
Docker image" status report to view the build results.

#### Build Universe Server locally

1. Validate and build the Universe artifacts
  ```bash
  scripts/build.sh
  ```

2. Build the Universe Server Docker image
  ```bash
  DOCKER_TAG="my-package" docker/server/build.bash
  ```
  This will create a Docker image `universe-server:my-package` and `docker/server/target/marathon.json` on your local machine

3. If you would like to publish the built Docker image, run
  ```bash
  DOCKER_TAG="my-package" docker/server/build.bash publish
  ```

#### Run Universe Server

Using the `marathon.json` that is created when building Universe Server we can run a Universe Server in our DC/OS
Cluster which can then be used to install packages.

Run the following commands to configure DC/OS to use the custom Universe Server (DC/OS 1.8+):

```bash
dcos marathon app add marathon.json
dcos package repo add --index=0 dev-universe http://universe.marathon.mesos:8085/repo
```

For DC/OS 1.7, a different URL must be used:

```bash
dcos marathon app add marathon.json
dcos package repo add --index=0 dev-universe http://universe.marathon.mesos:8085/repo-1.7
```

### Consumption Protocol

A DC/OS Cluster can be configured to point to multiple Universe Servers; each Universe Server will be fetched via
HTTPS or HTTP. When a DC/OS Cluster attempts to fetch the package set from a Universe Server, the Universe Server
will provide ONLY those packages which can be run on the cluster.

For example:
A DC/OS 1.6.1 Cluster will only receive packages with a `minDcosReleaseVersion` less than or equal to (`<=`) `1.6.1`
in the format the DC/OS Cluster expects.

```
 +----------------------+   +-----------------------+
 │public universe server│   │private universe server│
 +----------------------+   +-----------------------+
                http \         / http
                      \       /
                       \     /
                       +-----+           +--------+
                       │DC/OS│-----------│Marathon│
                       +-----+    http   +--------+
```

### Supported DC/OS Versions
Currently Universe Server provides support for the following versions of DC/OS

| DC/OS Release Version | Support Level |
|-----------------------|---------------|
| 1.6.1                 | Full Support  |
| 1.7                   | Full Support  |
| 1.8                   | Full Support  |
| 1.9                   | Full Support  |
| 1.10                  | Full Support  |
| 1.11                  | Full Support  |
