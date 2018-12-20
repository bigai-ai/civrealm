#Build freeciv-web from latest repo

import docker

def build_docker_img():
    client = docker.from_env()
    client.images.build(path="https://github.com/chris1869/freeciv-web.git#develop", tag="freeciv-web")
