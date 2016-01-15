#!/usr/bin/env python

import os
import sys
import json


class DuplicatedKeysException(Exception):
    pass


def json_checker(pair):
    ret = {}
    for key, value in pair:
        if key in ret:
            raise DuplicatedKeysException(
                "Duplicate key {!r} in json document".format(key))
        else:
            ret[key] = value
    return ret

if len(sys.argv) != 2:
    sys.stderr.write(
        "Syntax: {} path/to/file.json\n".format(os.path.basename(__file__)))
    sys.exit(1)

try:
    json.load(open(sys.argv[1]), object_pairs_hook=json_checker)
except DuplicatedKeysException as e:
    sys.stderr.write("Error validating %s: %s\n" % (sys.argv[1], e.args[0]))
    sys.exit(1)
