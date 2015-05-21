Universe Spec
=============

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

## MUST define a `package.json`

Schema: [package-schema.json](../repo/meta/schema/package-schema.json)

### MUST specify a unique `name` that is not used by any other package in the repo

### MUST specify a meaningful `version` that allows for targeted debugging

### MUST provide a meaningful `description` that will give the user insight into the service

### MUST provide a set of meaningful `tags` that will allow a user to search for the service

### MUST provide a `maintainer` property

### MUST specify a `images` object

1. All images SHOULD be free of visual artifacts such as JPG compression artifacts
1. All icons and schreenshots SHOULD provide a sibling resource for retina-ready displays (See [Retina Display Support](#Retina-Display-Support))
1. MUST provide URL for `icon-small` property (48px W x 48px H)
1. MUST provide URL for `icon-medium` property (96px W x 96px H)
1. MUST provide URL for `icon-large` property (256px W x 256px H)
1. MAY provide a set of `screenshots` (1200px W x 675px H)

### MAY specify a meaningful `preInstallNotes` property that will be displayed to the user prior to performing an install

### SHOULD specify a meaning `postInstallNotes` property that will be displayed to the user after performing an install

Good items to include are:
* Link to Service Documentation
* Link to Issue tracker for bug reports


## MUST define a `config.json`

Schema: [config-schema.json](../repo/meta/schema/config-schema.json)

### MUST namespace all properties

*A single `options.json` should be able to be used for an entire DCOS Cluster*

### MUST use hierarchical definition format

1. MUST set `additionalProperties` to `false` for all nested objects

### MUST mark all properties as required regardless of a default value being provided

This can be done with the `required: [...]` property that is sibling to `properties`

### SHOULD provide reasonable defaults for all properties

*mesos-dns names SHOULD be used whenever referring to another service in the cluster*

### MUST use standard property names when referring to global properties

1. MUST use `mesos.master` when referring to the Mesos Master zk URL
    * MUST use `zk://master.mesos:2181/mesos` for default value

### MUST reference all declared properties in `marathon.json`


## MUST define a `marathon.json`

Schema: [marathon-schema.json](../repo/meta/schema/marathon-schema.json)

Marathon App Definition: [AppDefinition.json](https://github.com/mesosphere/marathon/blob/master/src/main/resources/mesosphere/marathon/api/v2/AppDefinition.json)

Marathon App: [full-app.json](https://mesosphere.github.io/marathon/docs/rest-api.html#post-/v2/apps)

### MUST allow `id` to be configured

### MUST allow resources for scheduler to be configured

### MUST be able to run scheduler with only what is listed in marathon.json

* Docker Image
* Comprehensive URIs

### MUST define a health check for scheduler process

### SHOULD define a health check to expose the health of service tasks

* MUST set `maxConsecutiveFailures` to `0`
  * Ensures that Marathon does not attempt to restart scheduler due to unhealthy service tasks
  
### MUST reference all properties defined in `config.json`


## MAY define a `command.json`

Schema: [command-schema.json](../repo/meta/schema/command-schema.json)

### MUST define `pip: []`



## Resources

### Retina Display Support
To ensure your service icons look beautiful on retina-ready displays, please supply 2x versions of all icons.
No changes are needed to `package.json` - simply supply an additional icon file with the text `@2x` in the name before the file extension.

For example, the icon `https://downloads.mesosphere.io/cassandra-mesos/assets/cassandra-small.png` would have a retina-ready alternate image of `https://downloads.mesosphere.io/cassandra-mesos/assets/cassandra-small@2x.png`.

### DCOS Service Spec
....


### DCOS CLI Spec
....
