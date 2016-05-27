#!/usr/bin/env python3

import argparse
import base64
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

    universe = {
        'packages': [
            generate_package_from_path(
                args.repository,
                package_name,
                release_version)
            for package_name, release_version
            in enumerate_dcos_packages(args.repository)
        ]
    }

    universe_file_path = args.outdir / 'universe.json'

    with universe_file_path.open('w') as universe_file:
        json.dump(universe, universe_file)

    universe_old_zip = args.outdir / 'universe-1.6.1.zip'

    with tempfile.NamedTemporaryFile() as temp_file:
        with zipfile.ZipFile(temp_file, mode='w') as zip_file:
            render_universe_zip(zip_file, universe['packages'])

        shutil.copy(temp_file.name, str(universe_old_zip))


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
    if command and 'pip' in command:
        package['pip'] = command['pip']

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

    # TODO: What do we need to write?
    # write universe/repo/meta/index.json?
    # write universe/repo/meta/version.json?

    currentDir = pathlib.Path('universe')

    create_dir_in_zip(zip_file, currentDir)

    currentDir = currentDir / 'repo'
    create_dir_in_zip(zip_file, currentDir)

    currentDir = currentDir / 'packages'
    create_dir_in_zip(zip_file, currentDir)

    packages = sorted(
        packages,
        key=lambda package: (package['name'], package['releaseVersion']))

    currentLetter = ''
    currentPackageName = ''
    for package in packages:
        if currentLetter != package['name'][:1].upper():
            currentLetter = package['name'][:1].upper()
            create_dir_in_zip(zip_file, currentDir / currentLetter)

        if currentPackageName != package['name']:
            currentPackageName = package['name']
            create_dir_in_zip(
                zip_file,
                currentDir / currentLetter / currentPackageName)

        package_directory = (
            currentDir /
            currentLetter /
            currentPackageName /
            str(package['releaseVersion'])
        )
        create_dir_in_zip(zip_file, package_directory)

        write_package_in_zip(zip_file, package_directory, package)


def create_dir_in_zip(zip_file, directory):
    zip_file.writestr(str(directory) + '/', b'')


def write_package_in_zip(zip_file, path, package):
    package = package.copy()
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

    command = package.pop('pip', None)
    if command:
        zip_file.writestr(
            str(path / 'command.json'),
            json.dumps({'pip': command}))

    # TODO: Make sure that we don't have any extra fields like:
    # minDcosReleaseVersion
    zip_file.writestr(
        str(path / 'package.json'),
        json.dumps(package))


if __name__ == '__main__':
    sys.exit(main())
