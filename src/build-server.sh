#!/usr/bin/env python
#Build freeciv-web from latest repo

import docker

client = docker.from_env()
client.images.build(path="https://github.com/chris1869/freeciv-web.git#develop", tag="freeciv-web")
