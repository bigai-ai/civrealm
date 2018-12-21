#Build freeciv-web from latest repo
import docker

def build_docker_img():
    client = docker.from_env()
    print("Start building freeciv-web server. Take some coffee and relax. Takes up to 20minutes")
    cli = docker.APIClient(base_url='unix://var/run/docker.sock')
    for line in cli.build(path="https://github.com/chris1869/freeciv-web.git#develop", tag="freeciv-web"):
        if not "Downloading" in line:
            print line

#build_docker_img()
