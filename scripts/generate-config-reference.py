#!/usr/bin/env python3
"""This script builds a Markdown file containing configuration references for
all packages (and all package versions) contained in the Mesosphere DC/OS
Universe repository. It outputs a single file, 'config-reference.md' in the
current working directory.

  Usage:  ./generate-config-reference.py [/path/to/universe/repo/packages]

"""
import json
import os
import sys


def find_config_files(path):
    config_files = []

    for root, dirs, files in os.walk(path):
        for f in files:
            if f == 'config.json':
                config_files.append(os.path.join(root, f))

    return config_files


def main(path):
    files = find_config_files(path)
    config_ref_path = os.path.join(os.getcwd(), 'config-reference.md')
    outfile = open(config_ref_path, 'w', encoding='utf-8')
    outfile.write("# DC/OS Universe Package Configuration Reference\n\n")

    for f in files:
        with open(f, 'r', encoding='utf-8') as config:
            package_name = f.split('/')[-3]
            package_version = f.split('/')[-2]
            outfile.write("## {} version {}\n\n".format(package_name, package_version))
            props = json.loads(config.read())['properties']

            for key, value in props.items():
                if key == "properties":
                    outfile.write("*Errors encountered when processing config properties. Not all properties may be listed here. Please verify the structure of this package and package version.*\n\n")
                    continue

                outfile.write("### {} configuration properties\n\n".format(key))
                outfile.write("| Property | Type | Description | Default Value |\n")
                outfile.write("|----------|------|-------------|---------------|\n")

                for _, prop in value.items():
                    if type(prop) is not dict:
                        continue
                    for key, details in prop.items():
                        prop = key

                        try:
                            typ = details['type']
                        except KeyError:
                            typ = "*No type provided.*"

                        try:
                            desc = details['description']
                        except KeyError:
                            desc = "*No description provided.*"

                        try:
                            default = "`{}`".format(details['default'])
                            if default == "``":
                                default = "*Empty string.*"
                        except KeyError:
                            default = "*No default.*"

                        outfile.write("| {prop} | {typ} | {desc} | {default} |\n".format(
                            prop=prop, desc=desc, typ=typ, default=default))

                outfile.write("\n")

    outfile.close()

if __name__ == '__main__':
    if len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../repo/packages')

    main(path)
