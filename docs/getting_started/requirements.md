# Requirements

## Operating System

Civrealm works with the following operating systems:

* Windows >= `10`

* Ubuntu >= `20.0`

* macOS X

## Docker Version

CivRealm provides an interface for programmatic control of the Freeciv-web game. To run CivRealm locally, you need to start our customized Freeciv-web server using docker, which requires docker version >= `24.0.6`.

Check docker version by

```bash
docker -v
```

!!! note "Install Docker"
    We suggest following the [Docker Docs](https://docs.docker.com/engine/install/) to install the latest version of docker.

## Running Freeciv-web with Docker

!!! warning "Do not use the original Freeciv-web"
    Please do NOT use the image built based on the [original Freeciv-web repo](https://github.com/freeciv/freeciv-web). The image has been customize to suit agent training functionalities. The latest commits in that repo might cause compatibility issues.

There are 4 ways to start the customized Freeciv-web: use pull from docker hub, use our pre-built docker image directly or compile the docker image from source code.

### Method 1: Using civrealm's built-in commands (**Recommended**)

Remove the existing freeciv-web service as following:
```bash
remove_freeciv_web_service
```

Download the latest freeciv-web image as following:
```bash
download_freeciv_web_image
```

Start the freeciv-web service as following:
```bash
start_freeciv_web_service
```

To automatically remove the existing freeciv-web service, pull the latest freeciv-web image, and start the freeciv-web service, you can the following command:
```bash
build_freeciv_web_service
```

### Method 2: Pull from the Docker Hub

You can pull our pre-built docker image from docker hub. Suppose the image version is named as `VERSION`.

1. Pull the docker image to your local machine:
```bash
docker pull civrealm/freeciv-web:VERSION
```

2. Tag the docker image:
```bash
docker tag civrealm/freeciv-web:VERSION freeciv/freeciv-web:VERSION
```

3. Run the following command to clone Civrealm repo, and
build freeciv-web service from Docker:
```bash
git clone https://gitlab.mybigai.ac.cn/civilization/civrealm.git civrealm
cd civrealm/src/civrealm/configs
docker compose up -d freeciv-web
```

!!! tip "Docker permission"
    If the docker command complains about the sudo permission, please follow the instruction [here](https://askubuntu.com/questions/477551/how-can-i-use-docker-without-sudo).

!!! tip "command not found: docker compose"
    If the `docker compose` command is not found, please make sure that you have installed the docker version >= `24.0.6`.

!!! success "Freeciv-Web Service"
    After completing the above steps successfully, the freeciv-web service is started. You can connect to docker via host machine <a href="http://localhost:8080/">localhost:8080</a> using standard browser in general.

### Method 3: Use the Docker Image Directly

You can use our pre-built docker image file to directly start the Freeciv-web server, the steps are as follows:

1. Download our customized docker image from <a href="../releases/releases.html">here</a>. Suppose the downloaded image file is named as `IMAGE_FILE_NAME`.

2. Run the following command to load the downloaded docker image from the image file directory:
```bash
docker load -i IMAGE_FILE_NAME
```

3. Follow the step 3 of Method 2 to compose up service.

### Method 4: Compile the Docker Image from Source Code

You can also compile the source code to build the service follwing the instruction of Freeciv-web Repo from <a href="../releases/releases.html">here</a>. It has relatively large network overhead when building services, and could take a long time (up to 3 hours) to complete.
