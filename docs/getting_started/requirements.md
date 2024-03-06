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

There are 4 ways to download/build the customized Freeciv web image: 1. use CivRealm's built-in commands (recommended), 2. pull from the docker hub, 3. download and load our pre-built docker image, or 4. compile the docker image from source.

!!! success "Freeciv-Web Service"
    After starting the Freeciv-web service, you can connect to the Freeciv-web server via the host machine <a href="http://localhost:8080/">localhost:8080</a> using a standard browser.

### Method 1: Using CivRealm's built-in commands (**Recommended**)

1. Stop the existing freeciv-web service as follows. You can skip this step if you have not started the freeciv-web service before.

    ```bash
    stop_freeciv_web_service
    ```

    !!! note "Stop Container"
        This command keeps the image and only removes the container.

2. Download the latest freeciv-web image by the following command. You can skip this step if you have already downloaded the latest image.

    ```bash
    download_freeciv_web_image
    ```

3. Start the freeciv-web service by running:

    ```bash
    start_freeciv_web_service
    ```

We also provide a command `build_freeciv_web_service` that combines the above three commands for convenience. It automatically remove the existing freeciv-web service, fetch the latest freeciv-web image, and start the freeciv-web service.

### Method 2: Pull from the Docker Hub

You can pull our pre-built docker image from the docker hub. Assume the image version is named `VERSION'.

1. Pull the docker image to your local machine:

    ```bash
    docker pull civrealm/freeciv-web:VERSION
    ```

2. Tag the docker image:

    ```bash
    docker tag civrealm/freeciv-web:VERSION freeciv/freeciv-web:VERSION
    ```

3. Run the following command to clone the civrealm repo and build the
freeciv-web service from Docker:

    ```bash
    git clone ssh://git@gitlab.mybigai.ac.cn:2222/civilization/civrealm.git civrealm
    cd civrealm/src/civrealm/configs
    docker compose up -d freeciv-web
    ```

!!! tip "Docker permission"
    If the docker command complains about the sudo permission, please follow the instruction [here](https://askubuntu.com/questions/477551/how-can-i-use-docker-without-sudo).

!!! tip "command not found: docker compose"
    If the `docker compose` command is not found, please make sure that you have installed the docker version >= `24.0.6`.

### Method 3: Download and Load the Docker Image

You can use our pre-built docker image file to directly start the Freeciv-web server, the steps are as follows:

1. Download our customized docker image from <a href="../releases/releases.html">here</a>. Suppose the downloaded image file is named as `IMAGE_FILE_NAME`.

2. Run the following command to load the downloaded docker image from the image file directory:

```bash
docker load -i IMAGE_FILE_NAME
```

3. Follow the step 3 of Method 2 to start the docker service.

### Method 4: Compile the Docker Image from Source Code

You can also compile the source code to build the service follwing the instruction of Freeciv-web Repo from <a href="../releases/releases.html">here</a>. It has relatively large network overhead when building services, and could take a long time (up to 3 hours) to complete.
