#!/usr/bin/env python3

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile


def main():
    parser = argparse.ArgumentParser(
        description='This script is able to download the latest artifacts for '
        'all of the packages in the Universe repository into a zipfile. It '
        'uses a temporary file to store all of the artifacts as it downloads '
        'them because of this it requires that your temporary filesystem has '
        'enough space to store all of the artifact. You can control the path '
        'to the temporary file by setting the TMPDIR environment variable. '
        'E.g. TMPDIR=\'.\' ./scripts/local-universe.py ...')
    parser.add_argument(
        '--repository',
        required=True,
        help='Path to the top level package directory. E.g. repo/packages')
    parser.add_argument(
        '--sudo',
        action='store_true',
        default=False,
        help='Set this if sudo is required when executing the Docker CLI.')
    parser.add_argument(
        '--out-file',
        dest='outfile',
        required=True,
        help='Path to the zipfile to use to store all of the resources')
    parser.add_argument(
        '--include',
        default='',
        help='Command separated list of packages to include. If this option '
        'is not specified then all packages are downloaded. E.g. '
        '--include="marathon,chronos"')
    args = parser.parse_args()

    package_names = [name for name in args.include.split(',') if name != '']

    with zipfile.ZipFile(args.outfile, mode='w') as zip_file:
        for url, archive_path in ((url, archive_path)
                                  for package, path in
                                  enumerate_dcos_packages(
                                      pathlib.Path(args.repository),
                                      package_names)
                                  for url, archive_path in
                                  enumerate_http_resources(package, path)):
            add_http_resource(zip_file, url, archive_path)

        docker_images = [name
                         for _, path in
                         enumerate_dcos_packages(
                             pathlib.Path(args.repository),
                             package_names)
                         for name in
                         enumerate_docker_images(path)]

        for name in docker_images:
            download_docker_image(name, args.sudo)

        add_docker_images(zip_file, docker_images, args.sudo)


def enumerate_dcos_packages(packages_path, package_names):
    """Enumarate all of the package and revision to include

    :param packages_path: the path to the root of the packages
    :type pacakges_path: str
    :param package_names: list of package to include. empty list means all
                         packages
    :type package_names: [str]
    :returns: generator of package name and revision
    :rtype: gen((str, str))
    """

    for letter_path in packages_path.iterdir():
        assert len(letter_path.name) == 1 and letter_path.name.isupper()
        for package_path in letter_path.iterdir():

            largest_revision = max(
                package_path.iterdir(),
                key=lambda revision: int(revision.name))

            if not package_names or package_path.name in package_names:
                # Enumerate package if list is empty or package name in list
                yield (package_path.name, largest_revision)


def enumerate_http_resources(package, package_path):
    with (package_path / 'resource.json').open() as json_file:
        resource = json.load(json_file)

    for name, url in resource.get('images', {}).items():
        if name != 'screenshots':
            yield url, pathlib.PurePosixPath(package, 'images')

    for name, url in resource.get('assets', {}).get('uris', {}).items():
        yield url, pathlib.PurePosixPath(package, 'uris')


def enumerate_docker_images(package_path):
    with (package_path / 'resource.json').open() as json_file:
        resource = json.load(json_file)

    dockers = resource.get('assets', {}).get('container', {}).get('docker', {})

    return (name for _, name in dockers.items())


def download_docker_image(name, use_sudo):
    print('Pull docker images: {}'.format(name))
    command = ['docker', 'pull', name]

    command = ['sudo'] + command if use_sudo else command
    subprocess.call(command)


def add_http_resource(zip_file, url, dir_path):
    archive_path = (dir_path /
                    pathlib.PurePosixPath(urllib.parse.urlparse(url).path).name)
    print('Adding {} at {} to file zip.'.format(url, archive_path))
    with urllib.request.urlopen(url) as response:
        with tempfile.NamedTemporaryFile() as tempFile:
            shutil.copyfileobj(response, tempFile)
            tempFile.flush()
            zip_file.write(tempFile.name, str(archive_path))


def add_docker_images(zip_file, images, use_sudo):
    print('Saving docker images: {!r}'.format(images))
    with tempfile.NamedTemporaryFile() as tempFile:
        command = (
            ['docker', 'save', '--output={}'.format(tempFile.name)] +
            images
        )

        command = ['sudo'] + command if use_sudo else command

        subprocess.call(command)

        zip_file.write(tempFile.name, 'docker-images.tar')


if __name__ == '__main__':
    sys.exit(main())
