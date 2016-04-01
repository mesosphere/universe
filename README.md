# Mesosphere Universe [![Build Status](https://teamcity.mesosphere.io/guestAuth/app/rest/builds/buildType:(id:Oss_Universe_Ci)/statusIcon)](https://teamcity.mesosphere.io/viewType.html?buildTypeId=Oss_Universe_Ci&guest=1)

The DCOS package repository for packages that have been certified by Mesosphere.

## Installation

The latest [DCOS](https://mesosphere.com/product/) comes pre-configured to use the Universe
repository.

If you would like to add this to your DCOS manually:

```
dcos package repo add Universe https://universe.mesosphere.com/repo
```

## Branches

The default branch for this repository is `version-2.x`, which reflects the current schema for the
Universe. In the future, if the format changes significantly, there will be additional branches.

The `cli-tests-*` branches are used for integration testing by the [DCOS CLI](https://github.com/mesosphere/dcos-cli) and provides a fixed and well known set of packages to write tests against.

## Contributing a Package

Interested in making your package or service available to the world? The instructions below will
help you set up a local copy of the Universe for development.

### Development Set Up

1. Clone the repo (or you may wish to fork it first):

  ```
  git clone https://github.com/mesosphere/universe.git /path/to/universe
  ```

2. You may need to install the `jsonschema` Python package if you don't have it:

  ```
  sudo pip install jsonschema
  ```

3. Install pre-commit hook:

  ```
  bash /path/to/universe/scripts/install-git-hooks.sh
  ```

4. To test in DCOS we need to make the packages available to your cluster. We can do this using
topic or feature branches. Once you have committed your changes and pushed them to a topic branch.
We can use them within DCOS with:

  ```
  dcos package repo add Development http://github/path/to/branch/zip
  ```

  E.g. assuming the topic branch is named `topic-branch`:

  ```
  dcos package repo add Development https://github.com/mesosphere/universe/archive/topic-branch.zip
  ```

The pre-commit hook will run [build.sh](scripts/build.sh) before allowing you to commit. This
script validates your package definitions and regenerates the index file. You may need to
`git add repo/meta/index.json` after running it once before you are able to pass validation and
commit your changes.

### Submit to Universe

Before merging to Universe, you **must** run build.sh to regenerate the package index. If you
have installed the pre-commit hook as above, this will be done automatically on commit.

Once complete, please submit a pull request against the `version-2.x` branch with your changes.

Every pull request opened on this repo will have a set of automated verifications ran against it. 
These automated verification are reported against the pull request using the GitHub status API. 
All verifcations must pass in order for a pull request to be eligible for merge.

## Package entries

### Organization

Packages are encapsulated in their own directory, with one subdirectory for each package version.

```
└── foo
    ├── 0
    │   ├── command.json
    │   ├── config.json
    │   ├── marathon.json.mustache
 e  │   ├── resource.json
    │   └── package.json
    ├── 1
    │   ├── command.json
    │   ├── config.json
    │   ├── marathon.json.mustache
    │   ├── resource.json
    │   └── package.json
    └── ...

```
_Sample package directory layout._

### Content

#### `package.json`

```json
{
  "packagingVersion": "2.0",
  "name": "foo",
  "version": "1.2.3",
  "tags": ["mesosphere", "framework"],
  "maintainer": "help@bar.io",
  "description": "Does baz.",
  "scm": "https://github.com/bar/foo.git",
  "website": "http://bar.io/foo",
  "postInstallNotes": "Have fun foo-ing and baz-ing!"
}
```
_Sample `package.json`._

The required fields are:

- packagingVersion
- name
- version
- tags
- maintainer
- description

#### `config.json`

This file describes the configuration properties supported by the package. Each property can
specify whether or not it is required, a default value, as well as some basic validation.

Users can then [override specific values](https://docs.mesosphere.com/usage/service-config/) at
installation time by passing an options file to the DCOS CLI.

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
_Sample `config.json`._

`config.json` must be a valid [JSON Schema](http://json-schema.org/) file. Check out the
[JSON Schema examples](http://json-schema.org/examples.html).

#### `marathon.json.mustache`

This file describes how to run the package as a
[Marathon](http://github.com/mesosphere/marathon) app.

User-supplied metadata (as described in `config.json`), the defaults from `config.json` and the
resource information in `resource.json` will be injected to the template using
[mustache template](http://mustache.github.io/) syntax.

```json
{
  "id": "foo",
  "cpus": "1.0",
  "mem": "1024",
  "instances": "1",
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
_Sample `marathon.json.mustache`._

See the
[Marathon API Documentation](https://mesosphere.github.io/marathon/docs/rest-api.html)
for more detailed instruction on app definitions.

#### `command.json`

This file is **optional** and will soon be **deprecataed**. Please see `resource.json` for how
to specify binary CLIs instead. This file describes how to install the package's CLI from pip.
Specify where each element in the array is a line in the requirements file.

```json
{
  "pip": [
    "https://pypi.python.org/packages/source/f/foo/foo-1.2.3.tar.gz"
  ]
}
```
_Sample `command.json`._

See the [Command Schema](repo/meta/schema/command-schema.json) for a detailed description of
the schema.

#### `resource.json`

This file contains all of the externally hosted resources (E.g. Docker images, HTTP objects and
images, binary CLIs) needed to install the application.

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
  },
  "cli": {
    "binaries": {
      "linux": {
        "x86-64": {
          "kind": "executable",
          "url": "http://url/to/executable",
          "hashContents": [{
            "algo": "sha256",
            "value": "hash/of/contents"
          }]
        }
      }
    }
  }
}
```
_Sample `resource.json`._

For the Docker image, please use the image ID for the referenced image. You can find this by
pulling the image locally and running `docker images some-org/foo:1.0.0`.

For `cli.binaries`, we currently support windows, linux, and darwin platforms on x86-64 architecture.
A binary "kind" can either be an executable, or a zip file, with the executable in a top-level `bin` directory.
We currently only support sha256 as the hashing algorithm for verifying correctness of binary download.

While `images` is an optional field, it is highly recommended you include icons and screenshots
in your package and update the path definitions accordingly. Specifications are as follows:

* `icon-small`: 48px (w) x 48px (h)
* `icon-medium`: 96px (w) x 96px (h)
* `icon-large`: 256px (w) x 256px (h)
* `screenshots[...]`: 1200px (w) x 675px (h)

**NOTE:** To ensure your service icons look beautiful on retina-ready displays,
please supply 2x versions of all icons. No changes are needed to
`package.json` - simply supply an additional icon file with the text `@2x` in
the name before the file extension.
For example, the icon `icon-cassandra-small.png` would have a retina-ready
alternate image named `icon-cassandra-small@2x.png`.

See the [Resource Schema](repo/meta/schema/resource-schema.json) for a detailed description of
the schema.

### Versioning

The registry specification is versioned separately in the file `/repo/meta/version.json`.

```json
{
  "version": "2.0.0-rc2"
}
```
_Sample `repo/meta/version.json`._

This version is updated with any change to the required file content
(typically validated using JSON schema) or expected file organization in the
`repo` directory.

_NOTE: The current version is `2.0.0-rc2` to facilitate rapid
iteration.  This version will be fixed and incremented as
described above as programs that consume the format reach maturity._

The packaging version should also be included in the `package.json` for each package using the
`packagingVersion` property.

### Validation

Package content is validated using [JSON Schema](http://json-schema.org).
The schema definitions live in `/repo/meta/schema`.

## Directory Structure

```
├── LICENSE
├── README.md
├── docs
│   ├── best-practices.md
│   └── contributing.md
├── hooks
│   └── pre-commit
├── repo
│   ├── meta
│   │   ├── index.json
│   │   ├── schema
│   │   │   ├── command-schema.json
│   │   │   ├── config-schema.json
│   │   │   ├── index-schema.json
│   │   │   ├── resource-schema.json
│   │   │   └── package-schema.json
│   │   └── version.json
│   └── packages
│       ├── B
│       │   ├── bar
│       │   │   ├── 0
│       │   │   │   ├── command.json
│       │   │   │   ├── config.json
│       │   │   │   ├── marathon.json.mustache
│       │   │   │   ├── resource.json
│       │   │   │   └── package.json
│       │   │   └── ...
│       │   └── ...
│       ├── F
│       │   ├── foo
│       │   │   ├── 0
│       │   │   │   ├── config.json
│       │   │   │   ├── marathon.json.mustache
│       │   │   │   ├── resource.json
│       │   │   │   └── package.json
│       │   │   └── ...
│       │   └── ...
│       └── ...
└── scripts
    ├── 1-validate-packages.sh
    ├── 2-build-index.sh
    ├── 3-validate-index.sh
    ├── 4-detect-dependency-cycles.sh
    ├── build.sh
    └── install-git-hooks.sh
```

## Sources and Transfer Protocols

This section describes transfer of package metadata from a universe source to a client program.

```
 ┌───────────────┐   ┌────────────────┐
 │public universe│   │private universe│
 └───────────────┘   └────────────────┘
         http \         / http
               \       /
                \     /
               ┌────┐           ┌────────┐
               │DCOS│-----------│Marathon│
               └────┘    http   └────────┘
```
_Sample (simplified) architecture for a universe client program._

Package sources are described as URLs.

Source URLs encode the transfer protocol. Recommendations for several transfer protocols follow.

**HTTP and HTTPS**

A URL that designates a
[zip](http://en.wikipedia.org/wiki/Zip_%28file_format%29) file
accessible over HTTP or HTTPS with media type `application/zip`.
Example: `http://my.org/files/universe/packages.zip`
