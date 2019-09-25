# Universe Schema Files

This guides serves to explain the importance of each file in this folder.

## Universe CI specific files

This is the list of files used ONLY by Universe tooling

- `vX-repo-definitions.json` and related `*-repo-schema.json` files

    This file is used by Universe Server CI to generate and publish the Universe json files. This file also has shared definitions for `v3-repo-schema.json`, `v4-repo-schema.json`, and `v5-repo-schema.json`. This is used in [gen_universe.py](/scripts/gen_universe.py).

- `command-schema.json`

    This is used by [validate_packages.py](/scripts/validate_packages.py) to validate the universe packages in Pull Requests.

- `v2-resource-schema.json`

    This is used by [validate_packages.py](/scripts/validate_packages.py) to validate the universe packages in Pull Requests.

## Shared schema for Universe and Package Registry

This is the list of files used BOTH by Universe tooling and Package Registry

-  `config-schema.json`

    This is used by [validate_packages.py](/scripts/validate_packages.py) to validate the universe packages in Pull Requests. This is also used by package registry for validation and repo generation.

- `v3-resource-schema.json`

    This is used by [validate_packages.py](/scripts/validate_packages.py) to validate the universe packages in Pull Requests. This is also used by package registry for validation and repo generation.

## Package Registry specific schema

This is the list of files used ONLY by Package Registry. Both these files are converted to `golang` objects in Package Registry CLI and are defined in `Scala` in `cosmos-common` (which is used by Package Registry Server module)

- `metadata-schema.json`

    This is used to define the Universe Repository Metadata. Complied by package registry to serve the repository and also by cosmos to convert a Universe package to a package definition and vice-versa.

- `build-definition-schema.json`

    This is used to define the Package registry build definition (after a universe package migration). Used by package registry to serve the repository and also by cosmos to convert a Universe package to a package definition and vice-versa.

_PS: This directory should serve as single source of truth for schema definitions of DC/OS related packaging_
