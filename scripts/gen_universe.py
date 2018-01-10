#!/usr/bin/env python3

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
    create_content_type_file(ct_universe_path, "v4")

    # Render empty json
    empty_path = args.outdir / 'repo-empty-v3.json'
    with empty_path.open('w', encoding='utf-8') as universe_file:
        json.dump({'packages': []}, universe_file)
    ct_empty_path = args.outdir / 'repo-empty-v3.content_type'
    create_content_type_file(ct_empty_path, "v3")

    # create universe-by-version files for `dcos_versions`
    dcos_versions = ["1.6.1", "1.7", "1.8", "1.9", "1.10", "1.11"]
    [render_universe_by_version(
        args.outdir, packages, version) for version in dcos_versions]


def render_universe_by_version(outdir, packages, version):
    """Render universe packages for `version`. Zip files for versions < 1.8,
    and json files for version >= 1.8

    :param outdir: Path to the directory to use to store all universe objects
    :type outdir: str
    :param packages: package dictionary
    :type packages: dict
    :param version: DC/OS version
    :type version: str
    :rtype: None
    """

    if LooseVersion(version) < LooseVersion("1.8"):
        render_zip_universe_by_version(outdir, packages, version)
    else:
        file_path = render_json_by_version(outdir, packages, version)
        _validate_repo(file_path, version)
        render_content_type_file_by_version(outdir, version)


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


def render_content_type_file_by_version(outdir, version):
    """Render content type file for `version`

    :param outdir: Path to the directory to use to store all universe objects
    :type outdir: str
    :param version: DC/OS version
    :type version: str
    :rtype: None
    """

    universe_version = \
        "v3" if LooseVersion(version) < LooseVersion("1.10") else "v4"
    ct_file_path = \
        outdir / 'repo-up-to-{}.content_type'.format(version)
    create_content_type_file(ct_file_path, universe_version)


def create_content_type_file(path, universe_version):
    """ Creates a file with universe repo version `universe_version` content-type
    as its contents.

    :param path: the name of the content-type file
    :type path: str
    :param universe_version: Universe content type version: "v3" or "v4"
    :type universe_version: str
    :rtype: None
    """
    with path.open('w', encoding='utf-8') as ct_file:
        content_type = format_universe_repo_content_type(universe_version)
        ct_file.write(content_type)


def format_universe_repo_content_type(universe_version):
    """ Formats a universe repo content-type of version `universe-version`

    :param universe_version: Universe content type version: "v3" or "v4"
    :type universe_version: str
    :return: content-type of the universe repo version `universe_version`
    :rtype: str
    """
    content_type = "application/" \
                   "vnd.dcos.universe.repo+json;" \
                   "charset=utf-8;version=" \
                   + universe_version
    return content_type


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
        # that need to bridge versions must be accomodated.
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


def render_zip_universe_by_version(outdir, packages, version):
    """Render zip universe for `version`

    :param outdir: Path to the directory to use to store all universe objects
    :type outdir: str
    :param package: package dictionary
    :type package: dict
    :param version: DC/OS version
    :type version: str
    :rtype: None
    """

    with tempfile.NamedTemporaryFile() as temp_file:
        with zipfile.ZipFile(temp_file, mode='w') as zip_file:
            render_universe_zip(
                zip_file,
                filter(
                    lambda package: filter_by_version(package, version),
                    packages)
            )

        zip_name = 'repo-up-to-{}.zip'.format(version)
        shutil.copy(temp_file.name, str(outdir / zip_name))


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


def render_universe_zip(zip_file, packages):
    """Populates a zipfile from a list of universe v3 packages. This function
    creates directories to be backwards compatible with legacy Cosmos.

    :param zip_file: zipfile where we need to write the packages
    :type zip_file: zipfile.ZipFile
    :param packages: list of packages
    :type packages: [dict]
    :rtype: None
    """

    packages = sorted(
        packages,
        key=lambda package: (package['name'], package['releaseVersion']))

    root = pathlib.Path('universe')

    create_dir_in_zip(zip_file, root)

    create_dir_in_zip(zip_file, root / 'repo')

    create_dir_in_zip(zip_file, root / 'repo' / 'meta')
    zip_file.writestr(
        str(root / 'repo' / 'meta' / 'index.json'),
        json.dumps(create_index(packages)))

    zip_file.writestr(
        str(root / 'repo' / 'meta' / 'version.json'),
        json.dumps({'version': '2.0.0'}))

    packagesDir = root / 'repo' / 'packages'
    create_dir_in_zip(zip_file, packagesDir)

    currentLetter = ''
    currentPackageName = ''
    for package in packages:
        if currentLetter != package['name'][:1].upper():
            currentLetter = package['name'][:1].upper()
            create_dir_in_zip(zip_file, packagesDir / currentLetter)

        if currentPackageName != package['name']:
            currentPackageName = package['name']
            create_dir_in_zip(
                zip_file,
                packagesDir / currentLetter / currentPackageName)

        package_directory = (
            packagesDir /
            currentLetter /
            currentPackageName /
            str(package['releaseVersion'])
        )
        create_dir_in_zip(zip_file, package_directory)

        write_package_in_zip(zip_file, package_directory, package)


def create_dir_in_zip(zip_file, directory):
    """Create a directory in a zip file

    :param zip_file: zip file where the directory will get created
    :type zip_file: zipfile.ZipFile
    :param directory: path for the directory
    :type directory: pathlib.Path
    :rtype: None
    """

    zip_file.writestr(str(directory) + '/', b'')


def write_package_in_zip(zip_file, path, package):
    """Write packages files in the zip file

    :param zip_file: zip file where the files will get created
    :type zip_file: zipfile.ZipFile
    :param path: path for the package directory. E.g.
                 universe/repo/packages/M/marathon/0
    :type path: pathlib.Path
    :param package: package information dictionary
    :type package: dict
    :rtype: None
    """

    package = downgrade_package_to_v2(package)

    package.pop('releaseVersion')

    resource = package.pop('resource', None)
    if resource:
        zip_file.writestr(
            str(path / 'resource.json'),
            json.dumps(resource))

    marathon_template = package.pop(
        'marathon',
        {}
    ).get(
        'v2AppMustacheTemplate'
    )
    if marathon_template:
        zip_file.writestr(
            str(path / 'marathon.json.mustache'),
            base64.standard_b64decode(marathon_template))

    config = package.pop('config', None)
    if config:
        zip_file.writestr(
            str(path / 'config.json'),
            json.dumps(config))

    command = package.pop('command', None)
    if command:
        zip_file.writestr(
            str(path / 'command.json'),
            json.dumps(command))

    zip_file.writestr(
        str(path / 'package.json'),
        json.dumps(package))


def create_index(packages):
    """Create an index for all of the packages

    :param packages: list of packages
    :type packages: [dict]
    :rtype: dict
    """

    index = {
        'version': '2.0.0',
        'packages': [
            create_index_entry(same_packages)
            for _, same_packages
            in itertools.groupby(packages, key=lambda package: package['name'])
        ]
    }

    return index


def create_index_entry(packages):
    """Create index entry from packages with the same name.

    :param packages: list of packages with the same name
    :type packages: [dict]
    :rtype: dict
    """

    entry = {
        'versions': {}
    }

    for package in packages:
        entry.update({
            'name': package['name'],
            'currentVersion': package['version'],
            'description': package['description'],
            'framework': package.get('framework', False),
            'tags': package['tags'],
            'selected': package.get('selected', False)
        })

        entry['versions'][package['version']] = str(package['releaseVersion'])

    return entry


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


def downgrade_package_to_v2(package):
    """Converts a v4 or v3 package to a v2 package. If given a v2
    package, it creates a deep copy but does not modify it. It does not
    modify the original package.

    :param package: v4, v3, or v2 package
    :type package: dict
    :return: a v2 package
    :rtyte: dict
    """
    packaging_version = package.get("packagingVersion")
    if packaging_version == "2.0":
        return copy.deepcopy(package)
    elif packaging_version == "3.0":
        return v3_to_v2_package(package)
    else:
        return v3_to_v2_package(v4_to_v3_package(package))


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
    validator = jsonschema.Draft4Validator(_load_jsonschema(repo_version))
    errors = []
    for error in validator.iter_errors(repo_json_data):
        for suberror in sorted(error.context, key=lambda e: e.schema_path):
            errors.append('{}: {}'.format(list(suberror.schema_path), suberror.message))
    return errors


def _validate_repo(file_path, version):
    """Validates a repo JSON file against the given version.

    :param file_path: the path where the universe was stored
    :type file_path: str
    :param version: DC/OS version
    :type version: str
    :rtype: None
    """

    if LooseVersion(version) >= LooseVersion('1.10'):
        repo_version = 'v4'
    else:
        repo_version = 'v3'

    with file_path.open(encoding='utf-8') as repo_file:
        repo = json.loads(repo_file.read())

    errors = validate_repo_with_schema(repo, repo_version)
    if len(errors) != 0:
        sys.exit(
            'ERROR\n\nRepo {} version {} validation errors: {}'.format(
                file_path,
                repo_version,
                '\n'.join(errors)
            )
        )


def _load_jsonschema(repo_version):
    """Opens and parses the repo schema based on the version provided.

    :param repo_version: repo schema version. E.g. v3 vs v4
    :type repo_version: str
    :return: the schema dictionary
    :rtype: dict
    """

    with open(
        'repo/meta/schema/{}-repo-schema.json'.format(repo_version),
        encoding='utf-8'
    ) as schema_file:
        return json.loads(schema_file.read())


if __name__ == '__main__':
    sys.exit(main())
