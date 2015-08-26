#!/usr/bin/env python
import json
import sha
import sys


def PROVIDER_TMPL(provider):
    return {
        "name": provider,
        "url": provider + ".box",
        "checksum_type": "sha1",
        "checksum": sha.new(open(provider + ".box").read()).hexdigest()
    }

METADATA_TMPL = {
    "name": "ac-cloud",
    "description": "",
    "versions": [{
        "version": "0",
        "providers": []
    }]
}

for arg in sys.argv[1:]:
    METADATA_TMPL['versions'][0]['providers'].append(PROVIDER_TMPL(arg))

print(json.dumps(METADATA_TMPL, sort_keys=True, indent=2))
