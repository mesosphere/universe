# Universe

The Mesos package repository.

## Package entries

### Organization

Packages are encapsulated in their own directory, with one subdirectory
for each package version.

```
└── foo
    ├── 0
    │   ├── command.json
    │   ├── config.json
    │   ├── marathon.json
    │   └── package.json
    ├── 1
    │   ├── command.json
    │   ├── config.json
    │   ├── marathon.json
    │   └── package.json
    └── ...

```
_Sample package directory layout._

### Content

#### `package.json`

```json
{
  "name": "foo",
  "version": "1.2.3",
  "scm": "https://github.com/bar/foo.git",
  "maintainer": "help@bar.io",
  "description": "Does baz.",
  "website": "http://bar.io/foo",
  "dependencies": [
    { "name": "biz", "version": "1.2.+" }
  ],
  "postInstallNotes": "Have fun foo-ing and baz-ing!"
}
```
_Sample `package.json`._

#### `config.json`

```json
{
  "type": "object",
  "properties": {
    "foo.baz": {
      "type": "integer",
      "description": "How many times to do baz.",
      "minimum": 0,
      "maximum": 16,
      "required": false,
      "default": 4
    }
  },
  "required": ["foo.baz"]
}
```
_Sample `config.json`._

#### `marathon.json`

This file describes how to run the package as a
[Marathon](http://github.com/mesosphere/marathon) app.

User-supplied metadata (as described in `package.json`) can be injected
using [moustache template](http://mustache.github.io/) systax.

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
      "image": "bar/foo",
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
_Sample `marathon.json`._

See the
[Marathon API Documentation](https://mesosphere.github.io/marathon/docs/rest-api.html)
for more detailed instruction on app definitions.

#### `command.json`

This file is **optional**. Describes how to install the package's CLI.
Currently the only supported format is a Python egg.

```json
{
  "python": "https://pypi.python.org/packages/source/f/foo/foo-1.2.3.tar.gz"
}
```
_Sample `command.json`._

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
│   │   ├── index.json.gz
│   │   ├── schema
│   │   │   ├── command-schema.json
│   │   │   ├── config-schema.json
│   │   │   ├── index-schema.json
│   │   │   ├── marathon-schema.json
│   │   │   └── package-schema.json
│   │   └── version.json
│   └── packages
│       ├── B
│       │   ├── bar
│       │   │   ├── 0
│       │   │   │   ├── command.json
│       │   │   │   ├── config.json
│       │   │   │   ├── marathon.json
│       │   │   │   └── package.json
│       │   │   └── ...
│       │   └── ...
│       ├── F
│       │   ├── foo
│       │   │   ├── 0
│       │   │   │   ├── config.json
│       │   │   │   ├── marathon.json
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

This section describes transfer of package metadata from a universe
source to a client program.

```
 ┌───────────────┐   ┌────────────────┐
 │public universe│   │private universe│
 └───────────────┘   └────────────────┘
          git \         / http
               \       /
                \     /
               ┌──────┐           ┌────────┐
               │client│-----------│marathon│
               └──────┘    http   └────────┘
                  |
                  |
            ┌───────────┐
            │local cache│
            └───────────┘
```
_Sample (simplified) architecture for a universe client program._

Package sources are described as URLs.

Source URLs encode the transfer protocol.
Recommendations for several transfer protocols follow.

**Filesystem**

A URL that designates a local directory.  
Example: `file:///some/nfs/mount/universe`

**Git**

A URL that designates a git repository.  
Example: `git://github.com/mesosphere/universe.git`

**HTTP and HTTPS**

A URL that designates a [tar](http://savannah.gnu.org/projects/tar) file
accessible over HTTP or HTTPS.  
Example: `http://my.org/files/universe/packages.tgz`

