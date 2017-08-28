#!/usr/bin/env python3

import argparse
import concurrent.futures
import contextlib
import distutils.version
import fnmatch
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

HTTP_ROOT = "http://master.mesos:8082/"
DOCKER_ROOT = "master.mesos:5000"


def main():
    # Docker writes files into the tempdir as root, you need to be running
    # the script as root to clean these up successfully.
    if os.getuid() != 0:
        print("You must run this as root, please `sudo` first.")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description='This script is able to download the latest artifacts for '
        'all of the packages in the Universe repository into a docker image. '
        'You can control the path to the temporary file by setting the TMPDIR '
        'environment variable. E.g. TMPDIR=\'.\' ./scripts/local-universe.py '
        '...')
    parser.add_argument(
        '--server_url',
        default=HTTP_ROOT,
        help="URL for http server")
    parser.add_argument(
        '--repository',
        required=True,
        help='Path to the top level package directory. E.g. repo/packages')
    parser.add_argument(
        '--include',
        default='',
        help='Command separated list of packages to include. If this option '
        'is not specified then all packages are downloaded. E.g. '
        '--include="marathon,chronos"')
    parser.add_argument(
        '--selected',
        action='store_true',
        default=False,
        help='Set this to include only selected packages')
    parser.add_argument(
        '--nonlocal_images',
        action='store_true',
        default=False,
        help='Set this to leave images resource URLs untouched.')
    parser.add_argument(
        '--nonlocal_cli',
        action='store_true',
        default=False,
        help='Set this to leave CLI resource URLs untouched.')
    parser.add_argument(
        '--dcos_version',
        required=True,
        help='Set this to the version of DC/OS under which the local universe '
        'will operate. Ensures that only package versions compatible with '
        'that DC/OS version are included. This parameter is required.'
    )

    args = parser.parse_args()

    package_names = [name for name in args.include.split(',') if name != '']

    dcos_version = distutils.version.LooseVersion(args.dcos_version)

    with tempfile.TemporaryDirectory() as dir_path, \
            run_docker_registry(dir_path / pathlib.Path("registry")):

        http_artifacts = dir_path / pathlib.Path("http")
        docker_artifacts = dir_path / pathlib.Path("registry")
        repo_artifacts = dir_path / pathlib.Path("universe/repo/packages")

        # There is a race between creating this folder and docker run command
        # creating this volume
        os.makedirs(str(docker_artifacts), exist_ok=True)

        os.makedirs(str(http_artifacts))
        os.makedirs(str(repo_artifacts))

        failed_packages = []

        def handle_package(opts):
            package, path = opts
            try:
                prepare_repository(
                    package,
                    path,
                    pathlib.Path(args.repository),
                    repo_artifacts,
                    args.server_url,
                    args.nonlocal_images,
                    args.nonlocal_cli
                )

                for url, archive_path in enumerate_http_resources(
                    package,
                    path,
                    args.nonlocal_images,
                    args.nonlocal_cli
                ):
                    add_http_resource(http_artifacts, url, archive_path)

                for name in enumerate_docker_images(path):
                    download_docker_image(name)
                    upload_docker_image(name)
            except (subprocess.CalledProcessError, urllib.error.HTTPError):
                print('MISSING ASSETS: {}'.format(package))
                remove_package(package, dir_path)
                failed_packages.append(package)

            return package

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            for package in executor.map(
                handle_package,
                enumerate_dcos_packages(
                    pathlib.Path(args.repository),
                    package_names,
                    args.selected,
                    dcos_version)):
                print("Completed: {}".format(package))

        build_repository(
            pathlib.Path(
                os.path.dirname(os.path.realpath(__file__)),
                '..',
                'scripts'
            ),
            pathlib.Path(args.repository),
            pathlib.Path(dir_path, 'universe')
        )

        build_universe_docker(pathlib.Path(dir_path))

        if failed_packages:
            print("Errors: {}".format(failed_packages))
            print("These packages are not included in the image.")


def enumerate_dcos_packages(
        packages_path,
        package_names,
        only_selected,
        dcos_version):
    """Enumarate all of the package and revision to include

    :param packages_path: the path to the root of the packages
    :type packages_path: pathlib.Path
    :param package_names: list of package to include. empty list means all
                         packages
    :type package_names: [str]
    :param only_selected: filter the list of packages to only ones that are
                          selected
    :type only_selected: boolean
    :param: dcos_version: filter the list of packages to only ones compatible
                          with this DC/OS version; if None, do not filter
    :type dcos_version: distutils.version.LooseVersion | None
    :returns: generator of package name and revision
    :rtype: gen((str, pathlib.Path))
    """
    def version_check(package_json):
        if dcos_version:
            raw_version = package_json.get('minDcosReleaseVersion')
            if raw_version:
                min_version = distutils.version.LooseVersion(raw_version)
                if dcos_version < min_version:
                    return False
        return True


    def selected_check(package_name, package_json):
        if only_selected:
            return package_json.get('selected', False)
        return not package_names or package_name in package_names


    def include_revision(package_name, revision_path):
        json_path = revision_path / 'package.json'
        with json_path.open(encoding='utf-8') as json_file:
            package_json = json.load(json_file)

            version_pass = version_check(package_json)
            selected_pass = selected_check(package_name, package_json)

            return version_pass and selected_pass


    for letter_path in packages_path.iterdir():
        assert len(letter_path.name) == 1 and letter_path.name.isupper()

        for package_path in letter_path.iterdir():
            revision_paths = list(package_path.iterdir())
            revision_paths.sort(key=lambda r: int(r.name), reverse=True)

            # Include only the first acceptable revision
            for revision_path in revision_paths:
                if include_revision(package_path.name, revision_path):
                    yield (package_path.name, revision_path)
                    break


def enumerate_http_resources(package, package_path, skip_images, skip_cli):
    resource_path = package_path / 'resource.json'
    with resource_path.open(encoding='utf-8') as json_file:
        resource = json.load(json_file)

    if not skip_images:
        for name, url in resource.get('images', {}).items():
            if name != 'screenshots':
                yield url, pathlib.Path(package, 'images')

    for name, url in resource.get('assets', {}).get('uris', {}).items():
        yield url, pathlib.Path(package, 'uris')

    if not skip_cli:
        for os_type, arch_dict in \
                resource.get('cli', {}).get('binaries', {}).items():
            for arch in arch_dict.items():
                yield arch[1]['url'], pathlib.Path(package, 'uris', os_type)

    command_path = (package_path / 'command.json')
    if command_path.exists():
        with command_path.open(encoding='utf-8') as json_file:
            commands = json.load(json_file)

        for url in commands.get("pip", []):
            yield url, pathlib.Path(package, 'commands')


def enumerate_docker_images(package_path):
    resource_path = package_path / 'resource.json'
    with resource_path.open(encoding='utf-8') as json_file:
        resource = json.load(json_file)

    dockers = resource.get('assets', {}).get('container', {}).get('docker', {})

    return (name for _, name in dockers.items())


@contextlib.contextmanager
def run_docker_registry(volume_path):
    print('Start docker registry.')
    command = ['docker', 'run', '-d', '-p', '5000:5000', '--name',
               'registry', '-v', '{}:/var/lib/registry'.format(volume_path),
               'registry:2.4.1']

    subprocess.check_call(command)

    try:
        yield
    finally:
        print('Stopping docker registry.')
        command = ['docker', 'rm', '-f', 'registry']
        subprocess.call(command)


def download_docker_image(name):
    print('Pull docker images: {}'.format(name))
    command = ['docker', 'pull', name]

    subprocess.check_call(command)


def format_image_name(host, name):
    # Probably has a hostname at the front, get rid of it.
    if '.' in name.split(':')[0]:
        return '{}/{}'.format(host, "/".join(name.split("/")[1:]))

    return '{}/{}'.format(host, name)


def upload_docker_image(name):
    print('Pushing docker image: {}'.format(name))
    command = ['docker', 'tag', name,
               format_image_name('localhost:5000', name)]

    subprocess.check_call(command)

    command = ['docker', 'push', format_image_name('localhost:5000', name)]

    subprocess.check_call(command)


def build_universe_docker(dir_path):
    print('Building the universe docker container')
    current_dir = pathlib.Path(
        os.path.dirname(os.path.realpath(__file__)))
    shutil.copyfile(
        str(current_dir / '..' / 'docker' / 'local-universe' / 'Dockerfile'),
        str(dir_path / 'Dockerfile'))

    command = ['docker', 'build', '-t',
               'mesosphere/universe:{:.0f}'.format(time.time()),
               '-t', 'mesosphere/universe:latest', '.']

    subprocess.check_call(command, cwd=str(dir_path))


def add_http_resource(dir_path, url, base_path):
    archive_path = (dir_path / base_path /
                    pathlib.Path(urllib.parse.urlparse(url).path).name)
    print('Adding {} at {}.'.format(url, archive_path))
    os.makedirs(str(archive_path.parent), exist_ok=True)
    urllib.request.urlretrieve(url, str(archive_path))


def prepare_repository(
    package, package_path,
    source_repo, dest_repo,
    http_root,
    skip_images,
    skip_cli
):
    dest_path = dest_repo / package_path.relative_to(source_repo)
    shutil.copytree(str(package_path), str(dest_path))

    source_resource = package_path / 'resource.json'
    dest_resource = dest_path / 'resource.json'
    with source_resource.open(encoding='utf-8') as source_file, \
            dest_resource.open('w', encoding='utf-8') as dest_file:
        resource = json.load(source_file)

        # Change the root for images (ignore screenshots)
        if not skip_images and 'images' in resource:
            resource["images"] = {
                n: urllib.parse.urljoin(
                    http_root, str(pathlib.PurePath(
                        package, "images", pathlib.Path(uri).name)))
                for n, uri in resource.get("images", {}).items() if 'icon' in n}

        # Change the root for asset uris.
        if 'assets' in resource:
            resource["assets"]["uris"] = {
                n: urllib.parse.urljoin(
                    http_root, str(pathlib.PurePath(
                        package, "uris", pathlib.Path(uri).name)))
                for n, uri in resource["assets"].get("uris", {}).items()}

        # Change the root for cli uris.
        if not skip_cli and 'cli' in resource:
            for os_type, arch_dict in \
                    resource.get('cli', {}).get('binaries', {}).items():
                for arch in arch_dict.items():
                    uri = arch[1]["url"]
                    arch[1]["url"] = urllib.parse.urljoin(
                        http_root,
                        str(
                            pathlib.PurePath(
                                package,
                                "uris",
                                os_type,
                                pathlib.Path(uri).name)))

        # Add the local docker repo prefix.
        if 'assets' in resource:
            if 'container' in resource["assets"]:
                resource["assets"]["container"]["docker"] = {
                    n: format_image_name(DOCKER_ROOT, image_name)
                    for n, image_name in resource["assets"]["container"].get(
                        "docker", {}).items()}

        json.dump(resource, dest_file, indent=4)

    command_path = (package_path / 'command.json')
    if not command_path.exists():
        return

    dest_command = dest_path / 'command.json'
    with command_path.open(encoding='utf-8') as source_file, \
            dest_command.open('w', encoding='utf-8') as dest_file:
        command = json.load(source_file)

        command['pip'] = [
            urllib.parse.urljoin(
                http_root, str(pathlib.PurePath(
                    package, "commands", pathlib.Path(uri).name)))
            for uri in command.get("pip", [])
        ]
        json.dump(command, dest_file, indent=4)


def build_repository(scripts_dir, repo_dir, dest_dir):
    shutil.copytree(str(scripts_dir), str(dest_dir / "scripts"))
    shutil.copytree(str(repo_dir / '..' / 'meta'),
                    str(dest_dir / 'repo' / 'meta'))

    command = ["bash", "scripts/build.sh"]
    subprocess.check_call(command, cwd=str(dest_dir))


def remove_package(package, base_dir):
    for root, dirnames, filenames in os.walk(base_dir):
        for dirname in fnmatch.filter(dirnames, package):
            shutil.rmtree(os.path.join(root, dirname))


if __name__ == '__main__':
    sys.exit(main())
