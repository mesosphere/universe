#!/usr/bin/env python3
import os
from distutils.version import LooseVersion
import argparse
import base64
import collections
import copy
import itertools
import json
import jsonschema
import pathlib
import shutil
import sys
import tempfile
import re
import zipfile


dir_path = os.path.dirname(os.path.realpath(__file__))
schema_dir = os.environ.get("SCHEMA_DIR", "{}/../repo/meta/schema/".format(dir_path))
repo_definitions_json = "{}/vX-repo-definitions.json".format(schema_dir)


def main():
    parser = argparse.ArgumentParser(
        description='This script generates all of the universe objects from '
        'the universe repository. The files created in --out-dir are: '
        'universe.json.')
    parser.add_argument(
        '--repository',
        required=True,
        type=pathlib.Path,
        help='Path to the top level package directory. E.g. repo/packages')
    parser.add_argument(
        '--out-dir',
        dest='outdir',
        required=True,
        type=pathlib.Path,
        help='Path to the directory to use to store all universe objects')
    args = parser.parse_args()

    if not args.outdir.is_dir():
        print('The path in --out-dir [{}] is not a directory. Please create it'
              ' before running this script.'.format(args.outdir))
        return
    print('Paths present in [{}]: {}'.format(
        str(args.outdir),
        [str(p) for p in list(args.outdir.glob('*'))])
    )

    if not args.repository.is_dir():
        print('The path in --repository [{}] is not a directory.'.format(
            args.repository))
        return

    packages = [
        generate_package_from_path(
            args.repository,
            package_name,
            release_version)
        for package_name, release_version
        in enumerate_dcos_packages(args.repository)
    ]

    # Render entire universe
    universe_path = args.outdir / 'universe.json'
    with universe_path.open('w', encoding='utf-8') as universe_file:
        json.dump({'packages': packages}, universe_file)
    ct_universe_path = args.outdir / 'universe.content_type'
    create_content_type_file(ct_universe_path, "v5")

    # Render empty json
    empty_path = args.outdir / 'repo-empty-v3.json'
    with empty_path.open('w', encoding='utf-8') as universe_file:
        json.dump({'packages': []}, universe_file)
    ct_empty_path = args.outdir / 'repo-empty-v3.content_type'
    create_content_type_file(ct_empty_path, "v3")

    json_file_dcos_versions = ["1.8", "1.9", "1.10", "1.11", "1.12", "1.13", "2.0"]
    # create universe-by-version files for `json_file_dcos_versions`
    [render_universe_by_version(
        args.outdir, copy.deepcopy(packages), version) for version in json_file_dcos_versions]
    for dcos_version in json_file_dcos_versions:
        _populate_dcos_version_json_to_folder(dcos_version, args.outdir)


def get_universe_version_for_dcos(dcos_version):
    """Returns the highest packaging version supported for a DC/OS Version.
    1.9 and below  => v3
    1.11 and below => v4
    Latest version => v5

    :param dcos_version: The version of the DC/OS
    :type dcos_version: str
    :return The packaging version
    :rtype: str
    """
    if LooseVersion(dcos_version) <= LooseVersion("1.9"):
        return "v3"
    elif LooseVersion(dcos_version) <= LooseVersion("1.11"):
        return "v4"
    else:
        return "v5"


def render_universe_by_version(outdir, packages, version):
    """Render universe packages for `version`. Zip files for versions < 1.8
    are no longer updated. Use json files for version >= 1.8

    :param outdir: Path to the directory to use to store all universe objects
    :type outdir: str
    :param packages: package dictionary
    :type packages: dict
    :param version: DC/OS version
    :type version: str
    :rtype: None
    """

    if LooseVersion(version) < LooseVersion("1.8"):
        print("zip based universe files are no longer maintained")
    else:
        file_path = render_json_by_version(outdir, packages, version)
        _validate_repo(file_path, version)
        create_content_type_file(
            outdir / 'repo-up-to-{}.content_type'.format(version),
            get_universe_version_for_dcos(version)
        )


def json_escape_compatibility(schema: collections.OrderedDict) -> collections.OrderedDict:
    """ Further escape any singly escaped stringified JSON in config """

    for value in schema.values():
        if "description" in value:
            value["description"] = escape_json_string(value["description"])

        if "type" in value:
            if value["type"] == "string" and "default" in value:
                value["default"] = escape_json_string(value["default"])
            elif value["type"] == "object" and "properties" in value:
                value["properties"] = json_escape_compatibility(value["properties"])

    return schema


def escape_json_string(string: str) -> str:
    """ Makes any single escaped double quotes doubly escaped. """

    def escape_underescaped_slash(matchobj):
        """ Return adjacent character + extra escaped double quote. """
        return matchobj.group(1) + "\\\""

    # This regex means: match .\" except \\\" while capturing `.`
    return re.sub('([^\\\\])\\\"', escape_underescaped_slash, string)


def create_content_type_file(path, universe_version):
    """ Creates a file with universe repo version `universe_version` content-type
    as its contents.

    :param path: the name of the content-type file
    :type path: str
    :param universe_version: Universe content type version
    :type universe_version: str
    :rtype: None
    """
    with path.open('w', encoding='utf-8') as ct_file:
        ct_file.write(
            "application/vnd.dcos.universe.repo+json;" \
            "charset=utf-8;version={}".format(universe_version)
        )


def render_json_by_version(outdir, packages, version):
    """Render json file for `version`

    :param outdir: Path to the directory to use to store all universe objects
    :type outdir: str
    :param packages: package dictionary
    :type packages: dict
    :param version: DC/OS version
    :type version: str
    :return: the path where the universe was stored
    :rtype: str
    """

    packages = filter_and_downgrade_packages_by_version(packages, version)

    json_file_path = outdir / 'repo-up-to-{}.json'.format(version)
    with json_file_path.open('w', encoding='utf-8') as universe_file:
        json.dump({'packages': packages}, universe_file)

    return json_file_path


def filter_and_downgrade_packages_by_version(packages, version):
    """Filter packages by `version` and the downgrade if needed
    :param packages: package dictionary
    :type packages: dict
    :param version: DC/OS version
    :type version: str
    :return packages filtered (and may be downgraded) on `version`
    :rtype package dictionary
    """
    packages = [
        package for package in packages if filter_by_version(package, version)
    ]

    if LooseVersion(version) < LooseVersion('1.10'):
        # Prior to 1.10, Cosmos had a rendering bug that required
        # stringified JSON to be doubly escaped. This was corrected
        # in 1.10, but it means that packages with stringified JSON parameters
        # that need to bridge versions must be accommodated.
        #
        # < 1.9 style escaping:
        # \\\"field\\\": \\\"value\\\"
        #
        # >= 1.10 style escaping:
        # \"field\": \"value\"
        for package in packages:
            if "config" in package and "properties" in package["config"]:
                # The rough shape of a config file is:
                # {
                #   "schema": ...,
                #   "properties": { }
                # }
                # Send just the top level properties in to the recursive
                # function json_escape_compatibility.
                package["config"]["properties"] = json_escape_compatibility(
                    package["config"]["properties"])
        packages = [downgrade_package_to_v3(package) for package in packages]
    return packages


def filter_by_version(package, version):
    """Prediate for checking for packages of version `version` or less

    :param package: package dictionary
    :type package: dict
    :param version: DC/OS version
    :type version: str
    :rtype: bool
    """

    package_version = LooseVersion(
        package.get('minDcosReleaseVersion', '0.0')
    )

    filter_version = LooseVersion(version)

    return package_version <= filter_version


def package_path(root, package_name, release_version):
    """Returns the path to the package directory

    :param root: path to the root of the repository
    :type root: pathlib.Path
    :param package_name: name of the package
    :type package_name: str
    :param release_version: package release version
    :type release_version: int
    :rtype: pathlib.Path
    """

    return (root /
            package_name[:1].upper() /
            package_name /
            str(release_version))


def read_package(path):
    """Reads the package.json as a dict

    :param path: path to the package
    :type path: pathlib.Path
    :rtype: dict
    """

    path = path / 'package.json'
    with path.open(encoding='utf-8') as file_object:
        return json.load(file_object)


def read_resource(path):
    """Reads the resource.json as a dict

    :param path: path to the package
    :type path: pathlib.Path
    :rtype: dict | None
    """

    path = path / 'resource.json'

    if path.is_file():
        with path.open(encoding='utf-8') as file_object:
            return json.load(file_object)


def read_marathon_template(path):
    """Reads the marathon.json.mustache as a base64 encoded string

    :param path: path to the package
    :type path: pathlib.Path
    :rtype: str | None
    """

    path = path / 'marathon.json.mustache'

    if path.is_file():
        with path.open(mode='rb') as file_object:
            return base64.standard_b64encode(file_object.read()).decode()


def read_config(path):
    """Reads the config.json as a dict

    :param path: path to the package
    :type path: pathlib.Path
    :rtype: dict | None
    """

    path = path / 'config.json'

    if path.is_file():
        with path.open(encoding='utf-8') as file_object:
            # Load config file into a OrderedDict to preserve order
            return json.load(
                file_object,
                object_pairs_hook=collections.OrderedDict
            )


def read_command(path):
    """Reads the command.json as a dict

    :param path: path to the package
    :type path: pathlib.Path
    :rtype: dict | None
    """

    path = path / 'command.json'

    if path.is_file():
        with path.open(encoding='utf-8') as file_object:
            return json.load(file_object)


def generate_package_from_path(root, package_name, release_version):
    """Returns v3 package metadata for the specified package

    :param root: path to the root of the repository
    :type root: pathlib.Path
    :param package_name: name of the package
    :type package_name: str
    :param release_version: package release version
    :type release_version: int
    :rtype: dict
    """

    path = package_path(root, package_name, release_version)
    return generate_package(
        release_version,
        read_package(path),
        resource=read_resource(path),
        marathon_template=read_marathon_template(path),
        config=read_config(path),
        command=read_command(path)
    )


def generate_package(
        release_version,
        package,
        resource,
        marathon_template,
        config,
        command):
    """Returns v3 package object for package. See
    repo/meta/schema/v3-repo-schema.json

    :param release_version: package release version
    :type release_version: int
    :param package: content of package.json
    :type package: dict
    :param resource: content of resource.json
    :type resource: dict | None
    :param marathon_template: content of marathon.json.template as base64
    :type marathon_template: str | None
    :param config: content of config.json
    :type config: dict | None
    :param command: content of command.json
    :type command: dict | None
    :rtype: dict
    """

    package = package.copy()
    package['releaseVersion'] = release_version

    if resource:
        package['resource'] = resource
    if marathon_template:
        package['marathon'] = {
            'v2AppMustacheTemplate': marathon_template
        }
    if config:
        package['config'] = config
    if command:
        package['command'] = command

    return package


def enumerate_dcos_packages(packages_path):
    """Enumerate all of the package and release version to include

    :param packages_path: the path to the root of the packages
    :type packages_path: str
    :returns: generator of package name and release version
    :rtype: gen((str, int))
    """

    for letter_path in packages_path.iterdir():
        for package in letter_path.iterdir():
            for release_version in package.iterdir():
                yield (package.name, int(release_version.name))


def v3_to_v2_package(v3_package):
    """Converts a v3 package to a v2 package

    :param v3_package: a v3 package
    :type v3_package: dict
    :return: a v2 package
    :rtype: dict
    """
    package = copy.deepcopy(v3_package)

    package.pop('minDcosReleaseVersion', None)
    package['packagingVersion'] = "2.0"
    resource = package.get('resource', None)
    if resource:
        cli = resource.pop('cli', None)
        if cli and 'command' not in package:
            print(('WARNING: Removing binary CLI from ({}, {}) without a '
                  'Python CLI').format(package['name'], package['version']))

    return package


def v4_to_v3_package(v4_package):
    """Converts a v4 package to a v3 package

    :param v4_package: a v3 package
    :type v4_package: dict
    :return: a v3 package
    :rtype: dict
    """
    package = copy.deepcopy(v4_package)
    package.pop('upgradesFrom', None)
    package.pop('downgradesTo', None)
    package["packagingVersion"] = "3.0"
    return package


def downgrade_package_to_v3(package):
    """Converts a v4 package to a v3 package. If given a v3 or v2 package
    it creates a deep copy of it, but does not modify it. It does not
    modify the original package.

    :param package: v4, v3, or v2 package
    :type package: dict
    :return: a v3 or v2 package
    :rtyte: dict
    """
    packaging_version = package.get("packagingVersion")
    if packaging_version == "2.0" or packaging_version == "3.0":
        return copy.deepcopy(package)
    else:
        return v4_to_v3_package(package)


def validate_repo_with_schema(repo_json_data, repo_version):
    """Validates a repo and its version against the corresponding schema

    :param repo_json_data: The json of repo
    :param repo_version: version of the repo (e.g.: v4)
    :return: list of validation errors ( length == zero => No errors)
    """
    validator = jsonschema.Draft4Validator(
        _load_jsonschema(repo_version),
        resolver=jsonschema.RefResolver('file://' + repo_definitions_json, None))
    errors = []
    for error in validator.iter_errors(repo_json_data):
        for suberror in sorted(error.context, key=lambda e: e.schema_path):
            errors.append('{}: {}'.format(list(suberror.schema_path), suberror.message))
    return errors


def _populate_dcos_version_json_to_folder(dcos_version, outdir):
    """Populate the repo-up-to-<dcos-version>.json file to a folder.
    The folder structure would be :
        <dcos-version>/
            package/
                <name-of-package1>.json
                <name-of-package2>.json

    :param dcos_version: The version of DC/OS file to process.
    :type dcos_version: str
    :param outdir: Path to the directory to use to store all universe objects
    :type outdir: str
    :return: None
    """
    repo_dir = outdir / dcos_version / 'package'
    print('Paths present in [{}]: {}'.format(
        str(repo_dir),
        [str(p) for p in list(repo_dir.glob('*'))])
    )
    pathlib.Path(repo_dir).mkdir(parents=True)
    repo_file = pathlib.Path(outdir / 'repo-up-to-{}.json'.format(dcos_version))
    with repo_file.open('r',  encoding='utf-8') as f:
        data = json.loads(f.read())
        packages_dict = {}

        for package in data.get('packages'):
            package_name = package.get('name')
            package_list = packages_dict.get(package_name, [])
            package_list.append(package)
            packages_dict[package_name] = package_list

        for package_name, package_list in packages_dict.items():
            with pathlib.Path(repo_dir / '{}.json'.format(package_name))\
                        .open('w', encoding='utf-8') as f:
                json.dump({'packages': package_list}, f)


def _validate_repo(file_path, version):
    """Validates a repo JSON file against the given version.

    :param file_path: the path where the universe was stored
    :type file_path: str
    :param version: DC/OS version
    :type version: str
    :rtype: None
    """
    with file_path.open(encoding='utf-8') as repo_file:
        repo = json.loads(repo_file.read())

    errors = validate_repo_with_schema(
        repo,
        get_universe_version_for_dcos(version)
    )
    if len(errors) != 0:
        sys.exit(
            'ERROR\n\nRepo {} version {} validation errors: {}'.format(
                file_path,
                version,
                '\n'.join(errors)
            )
        )


def _load_jsonschema(repo_version):
    """Opens and parses the repo schema based on the version provided.

    :param repo_version: repo schema version
    :type repo_version: str
    :return: the schema dictionary
    :rtype: dict
    """
    with open(
        '{}/{}-repo-schema.json'.format(schema_dir, repo_version),
        encoding='utf-8'
    ) as schema_file:
        return json.loads(schema_file.read())


if __name__ == '__main__':
    sys.exit(main())
