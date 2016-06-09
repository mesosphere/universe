#!/usr/bin/env python3

import json
import jsonschema
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.realpath(__file__))
UNIVERSE_DIR = os.path.join(SCRIPTS_DIR, "..")
PKG_DIR = os.path.join(UNIVERSE_DIR, "repo/packages")
SCHEMA_DIR = os.path.join(UNIVERSE_DIR, "repo/meta/schema")


def _get_json_schema(file_name):
    with open(os.path.join(SCHEMA_DIR, file_name)) as f:
        return json.loads(f.read())

PACKAGE_JSON_SCHEMA = _get_json_schema('package-schema.json')
COMMAND_JSON_SCHEMA = _get_json_schema('command-schema.json')
CONFIG_JSON_SCHEMA = _get_json_schema('config-schema.json')
V2_RESOURCE_JSON_SCHEMA = _get_json_schema('v2-resource-schema.json')
V3_RESOURCE_JSON_SCHEMA = _get_json_schema('v3-resource-schema.json')


def main():
    # traverse prefix dirs ("A", "B", etc)
    for letter in os.listdir(PKG_DIR):
        prefix_path = os.path.join(PKG_DIR, letter)
        # traverse each package dir directory (ie "cassandra")
        for given_package in os.listdir(prefix_path):
            package_path = os.path.join(prefix_path, given_package)
            _validate_package(given_package, package_path)

    print("\nEverything OK!")


def _validate_package(given_package, path):
    print("Validating {}...".format(given_package))
    for rev in os.listdir(path):
        _validate_revision(given_package, rev, os.path.join(path, rev))


def _validate_revision(given_package, revision, path):
    print("\tValidating revision {}...".format(revision))

    # validate package.json
    package_json_path = os.path.join(path, 'package.json')
    print("\t\tpackage.json:", end='')
    if not os.path.isfile(package_json_path):
        sys.exit("\tERROR\n\nMissing required package.json file")
    package_json = _validate_json(package_json_path, PACKAGE_JSON_SCHEMA)
    print("\tOK")

    packaging_version = package_json.get("packagingVersion", "2.0")

    # validate command.json
    command_json_path = os.path.join(path, 'command.json')
    if os.path.isfile(command_json_path):
        print("\t\tcommand.json:", end='')
        _validate_json(command_json_path, COMMAND_JSON_SCHEMA)
        print("\tOK")

    # validate config.json
    config_json_path = os.path.join(path, 'config.json')
    if os.path.isfile(config_json_path):
        print("\t\tconfig.json:", end='')
        _validate_json(config_json_path, CONFIG_JSON_SCHEMA)
        print("\tOK")

    # validate existence of required marathon.json for v2
    if packaging_version == "2.0":
        marathon_json_path = os.path.join(path, 'marathon.json.mustache')
        print("\t\tmarathon.json.mustache:", end='')
        if not os.path.isfile(marathon_json_path):
            sys.exit("\tERROR\n\nMissing required marathon.json.mustache")
        print("\tOK")

    # validate resource.json
    resource_json_path = os.path.join(path, 'resource.json')
    if os.path.isfile(resource_json_path):
        print("\t\tresource.json:", end='')
        if packaging_version == "2.0":
            _validate_json(resource_json_path, V2_RESOURCE_JSON_SCHEMA)
        else:
            _validate_json(resource_json_path, V3_RESOURCE_JSON_SCHEMA)
        print("\tOK")


def _validate_json(path, schema):
        with open(path) as f:
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
