#!/usr/bin/env python3
import sys
from json import dump
from pathlib import Path


def exit(code, message):
    print(message, file=sys.stderr)
    sys.exit(code)


try:
    from ruamel.yaml import YAML
    load = YAML(typ='safe').load
except ImportError as e:
    print("WARNING:", e)
    try:
        from yaml import safe_load as load
    except ImportError as e:
        print("WARNING:", e)
        exit(1, "No YAML libraries found!")


argc = len(sys.argv)
if argc < 2 or argc > 3:
    exit(0, "usage: {sys.argv[0]} yaml_file [json_file]")

yfile = Path(sys.argv[1])
if not yfile.exists():
    exit(1, f"YAML file doesn't exists: {yfile}")

jfile = yfile.with_suffix('.json') if argc == 2 else Path(sys.argv[2])
if jfile.exists():
    exit(1, f"JSON file already exists: {jfile}")

with open(str(yfile)) as in_,  open(str(jfile), 'w') as out:
    dump(load(in_), out, indent='\t')

exit(0, f"{yfile} -> {jfile}")
