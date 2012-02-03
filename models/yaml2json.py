#!/usr/bin/python3

import yaml, json, sys

inputData = sys.stdin.read(-1)
data = yaml.load(inputData)
output = json.dumps(data)

print(output)

