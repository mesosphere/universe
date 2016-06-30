#!/usr/bin/env python3

from distutils.version import LooseVersion
import argparse
import base64
import itertools
import json
import pathlib
import shutil
import sys
import tempfile
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
        print('The path in --out-dir [{}] is not a directory. Please create it '
              'before running this script.'.format(args.outdir))
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
    with (args.outdir / 'universe.json').open('w') as universe_file:
        json.dump({'packages': packages}, universe_file)

    # Render empty json
    with (args.outdir / 'repo-empty-v3.json').open('w') as universe_file:
        json.dump({'packages': []}, universe_file)

    # Render 1.8 json
    with (args.outdir / 'repo-up-to-1.8.json').open('w') as universe_file:
        json.dump(
            {'packages': list(filter(filter_1_8, packages))},
            universe_file)

    # Render zip universe for 1.6.1
    with tempfile.NamedTemporaryFile() as temp_file:
        with zipfile.ZipFile(temp_file, mode='w') as zip_file:
            render_universe_zip(
                zip_file,
                filter(filter_1_6_1, packages)
            )

        shutil.copy(temp_file.name, str(args.outdir / 'repo-up-to-1.6.1.zip'))

    # Render zip universe for 1.7
    with tempfile.NamedTemporaryFile() as temp_file:
        with zipfile.ZipFile(temp_file, mode='w') as zip_file:
            render_universe_zip(
                zip_file,
                filter(filter_1_7, packages)
            )

        shutil.copy(temp_file.name, str(args.outdir / 'repo-up-to-1.7.zip'))


def filter_1_6_1(package):
    """Predicate for checking for 1.6.1 or less packages

    :param package: package dictionary
    :type package: dict
    :rtype: bool
    """

    package_version = LooseVersion(
        package.get('minDcosReleaseVersion', '0.0')
    )

    filter_version = LooseVersion("1.6.1")

    return package_version <= filter_version


def filter_1_7(package):
    """Predicate for checking for 1.7 or less packages

    :param package: package dictionary
    :type package: dict
    :rtype: bool
    """

    package_version = LooseVersion(
        package.get('minDcosReleaseVersion', '0.0')
    )

    filter_version = LooseVersion("1.7")

    return package_version <= filter_version


def filter_1_8(package):
    """Predicate for checking for 1.8 or less packages

    :param package: package dictionary
    :type package: dict
    :rtype: bool
    """

    package_version = LooseVersion(
        package.get('minDcosReleaseVersion', '0.0')
    )

    filter_version = LooseVersion("1.8")

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

    with path.open() as file_object:
        return json.load(file_object)


def read_resource(path):
    """Reads the resource.json as a dict

    :param path: path to the package
    :type path: pathlib.Path
    :rtype: dict | None
    """

    path = path / 'resource.json'

    if path.is_file():
        with path.open() as file_object:
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
    """Reads the resource.json as a dict

    :param path: path to the package
    :type path: pathlib.Path
    :rtype: dict | None
    """

    path = path / 'config.json'

    if path.is_file():
        with path.open() as file_object:
            return json.load(file_object)


def read_command(path):
    """Reads the command.json as a dict

    :param path: path to the package
    :type path: pathlib.Path
    :rtype: dict | None
    """

    path = path / 'command.json'

    if path.is_file():
        with path.open() as file_object:
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
        command=read_command(path))


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
    package['command'] = command

    return package


def enumerate_dcos_packages(packages_path):
    """Enumarate all of the package and release version to include

    :param packages_path: the path to the root of the packages
    :type pacakges_path: str
    :returns: generator of package name and release version
    :rtype: gen((str, int))
    """

    for letter_path in packages_path.iterdir():
        assert len(letter_path.name) == 1 and letter_path.name.isupper()
        for package_path in letter_path.iterdir():
            for release_version in package_path.iterdir():
                yield (package_path.name, int(release_version.name))


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

    package = package.copy()
    package.pop('releaseVersion')
    package.pop('minDcosReleaseVersion', None)
    package['packagingVersion'] = "2.0"

    resource = package.pop('resource', None)
    if resource:
        cli = resource.pop('cli', None)
        if cli and 'command' not in package:
            print(('WARNING: Removing binary CLI from ({}, {}) without a '
                  'Python CLI').format(package['name'], package['version']))
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


if __name__ == '__main__':
    sys.exit(main())
