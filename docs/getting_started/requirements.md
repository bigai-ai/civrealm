# Requirements

## Docker Version

Civrealm requires docker version >= `24.0.6`.

!!! note "Install Docker"
    We suggest following the [Docker Docs](https://docs.docker.com/engine/install/) to install the latest version of docker.

## Running Freeciv-web on Docker

!!! warning "Do not use the original Freeciv-web"
    Please do NOT use the image built based on the [original Freeciv-web repo](https://github.com/freeciv/freeciv-web). The image has been customize to suit agent training functionalities. The latest commits in that repo might cause compatibility issues.

CivRealm provides an interface for programmatic control of the Freeciv-web game. 

To test CivRealm locally, there are 2 ways to build freeciv-web service. 

1. compile the source code to build the service follwing the instruction of Freeciv-web Repo from <a href="../releases/releases.html">here</a>;

2. use the generated image file directly to start the service.

The former has relatively large network overhead when building services, and usually takes 1 to 3 hours to complete. 

If the file download speed is faster, we suggest follwing the second method to start the service, the steps are as follows:

1. Download our customized docker image `File` from <a href="../releases/releases.html">here</a>.

2. Run the following command to load the downloaded docker image from the image file directory:
```bash
docker load -i $IMAGE_FILE_NAME
```

3. Run the following command to clone Civrealm repo, and
build freeciv-web service from Docker:
```bash
git clone https://gitlab.mybigai.ac.cn/civilization/civrealm.git civrealm
cd civrealm
docker compose up -d
```

!!! tip "Docker permission"
    If the docker command complains about the sudo permission, please follow the instruction [here](https://askubuntu.com/questions/477551/how-can-i-use-docker-without-sudo).

After completing the above steps successfully, the freeciv-web service is started. You can connect to docker via host machine <a href="http://localhost:8080/">localhost:8080</a> using standard browser in general.
