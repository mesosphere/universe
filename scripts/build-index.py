#!/usr/bin/env python

import collections
import json
import os
import sys


def main():

    if len(sys.argv) is not 2:
        print('Usage: build-index.py /path/to/universe')
        return 1

    repo_dir = sys.argv[1]

    index = build_index(repo_dir)

    # Write the index file
    index_file = os.path.join(repo_dir, 'repo', 'meta', 'index.json')
    write_pretty_json(index_file, index)

    return 0


def build_index(repo_dir):

    packages_dir = os.path.join(repo_dir, 'repo', 'packages')

    # Extract universe version.
    version_file = os.path.join(repo_dir, 'repo', 'meta', 'version.json')
    version_json = read_json(version_file)
    version = version_json['version']

    # Build index entries.
    package_dirs = [p for d in os.listdir(packages_dir)
                    for p in os.listdir(os.path.join(packages_dir, d))]

    index_entries = [make_index_entry(
        os.path.join(
            repo_dir,
            'repo',
            'packages',
            dir[0].title(),
            dir
        )
    ) for dir in package_dirs if not dir.startswith('.')]

    index_entries.sort(key=lambda p: p.get('name', ''))

    index = {
        'version': version,
        'packages': index_entries
    }

    return index


def make_index_entry(package_dir):

    def is_version_dir(d):
        is_dir = os.path.isdir(os.path.join(package_dir, d))
        starts_with_dot = d.startswith('.')
        return is_dir and not starts_with_dot

    package_versions = sorted(
        filter(is_version_dir, os.listdir(package_dir)),
        key=int)

    entry = collections.OrderedDict()
    entry['versions'] = collections.OrderedDict()

    for v in package_versions:
        package_metadata_file = os.path.join(package_dir, v, 'package.json')
        package_metadata = read_json(package_metadata_file)

        software_version = package_metadata['version']

        is_framework = package_metadata.get('framework')
        if is_framework is None:
            is_framework = False

        entry.update({
            'name':           package_metadata['name'],
            'currentVersion': software_version,
            'description':    package_metadata['description'],
            'framework':      is_framework,
            'tags':           package_metadata['tags'],
            'selected':       package_metadata.get('selected', False)

        })
        entry['versions'][software_version] = v

    return entry


def read_json(path):
    with open(path) as json_file:
        return json.load(json_file)


def write_pretty_json(path, data):
    with open(path, 'w') as fd:
        fd.write(json.dumps(data,
                            sort_keys=True,
                            separators=(',', ':'),
                            indent=2) + '\n')
        fd.flush()
        os.fsync(fd)


if __name__ == "__main__":
    main()
