#Build freeciv-web from latest repo
import docker
import os

def build_docker_img():
    client = docker.from_env()
    print("Start building freeciv-web server. Take some coffee and relax. Takes up to 20minutes")
    cli = docker.APIClient(base_url='unix://var/run/docker.sock')
    for line in cli.build(path="https://github.com/freeciv/freeciv-web.git#develop", tag="freeciv-web"):                          
        if not "Downloading" in line.decode('utf-8'):
            print(line)
