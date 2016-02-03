import json

__author__ = "Aaron Eppert <aaron.eppert@packetsled.com>"


def process(options, results, output_handle):
    output_handle.write(json.dumps(results) + "\n")