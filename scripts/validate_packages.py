#!/usr/bin/env python3

import json
import jsonschema
import os
import re
import sys
from distutils.version import LooseVersion

SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))
UNIVERSE_DIR = os.path.join(SCRIPTS_DIR, "..")
PKG_DIR = os.path.join(UNIVERSE_DIR, "repo/packages")
SCHEMA_DIR = os.path.join(UNIVERSE_DIR, "repo/meta/schema")
LETTER_PATTERN = re.compile("^[A-Z]$")
PACKAGE_FOLDER_PATTERN = re.compile("^[a-z][a-z0-9-]*[a-z0-9]$")


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def _get_json_schema(file_name):
    with open(os.path.join(SCHEMA_DIR, file_name), encoding='utf-8') as f:
        return json.loads(f.read())

PACKAGE_JSON_SCHEMA = _get_json_schema('package-schema.json')
COMMAND_JSON_SCHEMA = _get_json_schema('command-schema.json')
CONFIG_JSON_SCHEMA = _get_json_schema('config-schema.json')
V2_RESOURCE_JSON_SCHEMA = _get_json_schema('v2-resource-schema.json')
V3_RESOURCE_JSON_SCHEMA = _get_json_schema('v3-resource-schema.json')


def main():
    # traverse prefix dirs ("A", "B", etc)
    for letter in os.listdir(PKG_DIR):
        if not LETTER_PATTERN.match(letter):
            sys.exit(
                "\tERROR\n\n"
                "Invalid name for directory : {}\nName should match the "
                "pattern : {}".format(letter, LETTER_PATTERN.pattern)
            )
        prefix_path = os.path.join(PKG_DIR, letter)
        # traverse each package dir directory (e.g., "cassandra")
        for given_package in os.listdir(prefix_path):
            package_path = os.path.join(prefix_path, given_package)
            _validate_package(given_package, package_path)

    eprint("\nEverything OK!")


def _validate_package(given_package, path):
    eprint("Validating {}...".format(given_package))
    for rev in os.listdir(path):
        _validate_revision(given_package, rev, os.path.join(path, rev))


def _validate_revision(given_package, revision, path):
    eprint("\tValidating revision {}...".format(revision))

    # validate package.json
    package_json_path = os.path.join(path, 'package.json')
    eprint("\t\tpackage.json:", end='')
    if not os.path.isfile(package_json_path):
        sys.exit("\tERROR\n\nMissing required package.json file")
    package_json = _validate_json(package_json_path, PACKAGE_JSON_SCHEMA)
    package_name = package_json.get("name")
    _validate_package_with_directory(given_package, package_name)
    eprint("\tOK")

    packaging_version = package_json.get("packagingVersion", "2.0")

    # validate upgrades version
    min_dcos_release_version = package_json.get("minDcosReleaseVersion", "0.0")
    upgrades_from = package_json.get("upgradesFrom", None)
    downgrades_to = package_json.get("downgradesTo", None)
    if (packaging_version == "4.0" and
            (upgrades_from or downgrades_to) and
            LooseVersion(min_dcos_release_version) < LooseVersion("1.10")):
        # Note: We are going to allow this package state and as a result the
        # conversion from v4 to v3. Even though this conversion loses
        # information, the only consumers of the Universe repo API is "Cosmos
        # the service manager". Old (< 1.10) Cosmos client don't implement the
        # update API and new Cosmos (>= 1.10), which implement the update API
        # will use the new repo media type.
        #
        # It is important that "package managers" (e.g. Local Universe) cannot
        # see this converted package and instead always see the original v4
        # package.
        pass

    # validate command.json
    command_json_path = os.path.join(path, 'command.json')
    command_json = None
    if os.path.isfile(command_json_path):
        eprint("\t\tcommand.json:", end='')
        if packaging_version == "4.0":
            sys.exit(
                "\tERROR\n\n"
                "Command file is not support for version 4.0 packages"
            )
        else:
            command_json = _validate_json(
                command_json_path,
                COMMAND_JSON_SCHEMA
            )
        eprint("\tOK")

    # validate config.json
    config_json_path = os.path.join(path, 'config.json')
    if os.path.isfile(config_json_path):
        eprint("\t\tconfig.json:", end='')
        _validate_json(config_json_path, CONFIG_JSON_SCHEMA)
        eprint("\tOK")

    # validate existence of required marathon.json for v2
    if packaging_version == "2.0":
        marathon_json_path = os.path.join(path, 'marathon.json.mustache')
        eprint("\t\tmarathon.json.mustache:", end='')
        if not os.path.isfile(marathon_json_path):
            sys.exit("\tERROR\n\nMissing required marathon.json.mustache")
        eprint("\tOK")

    # validate resource.json
    resource_json_path = os.path.join(path, 'resource.json')
    resource_json = None
    if os.path.isfile(resource_json_path):
        eprint("\t\tresource.json:", end='')
        if packaging_version == "2.0":
            resource_json = _validate_json(
                resource_json_path,
                V2_RESOURCE_JSON_SCHEMA)
        else:
            resource_json = _validate_json(
                resource_json_path,
                V3_RESOURCE_JSON_SCHEMA)
        eprint("\tOK")

    # Validate that we don't drop information during the conversion
    old_package = LooseVersion(
        package_json.get('minDcosReleaseVersion', "1.0")) < LooseVersion("1.8")
    if (old_package and resource_json and 'cli' in resource_json and
            command_json is None):
        sys.exit('\tERROR\n\nA package with CLI specified in resource.json is '
                 'only supported when minDcosReleaseVersion is greater than '
                 '1.8.')


def _validate_package_with_directory(given_package, actual_package_name):
    if not PACKAGE_FOLDER_PATTERN.match(given_package):
        sys.exit(
            "\tERROR\n\n"
            "Invalid name for package directory : {}"
            "\nName should match the pattern : {}"
            .format(given_package, PACKAGE_FOLDER_PATTERN.pattern)
        )
    if given_package != actual_package_name:
        sys.exit(
            "\tERROR\n\n"
            "The name parameter in package.json should match with the name of "
            "the package directory.\nDirectory : {}, Parsed Name : {}"
            .format(given_package, actual_package_name)
        )


def _validate_json(path, schema):
        with open(path, encoding='utf-8') as f:
            data = json.loads(f.read())

        _validate_jsonschema(data, schema)
        return data


def _validate_jsonschema(instance, schema):
    validator = jsonschema.Draft4Validator(schema)
    errors = list(validator.iter_errors(instance))
    if len(errors) != 0:
        sys.exit("\tERROR\n\nValidation error: {}".format(errors))


if __name__ == '__main__':
    sys.exit(main())
