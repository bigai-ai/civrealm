# System Requirements


## Python Version
Civrealm requires Python version >=3.8. If you are using [Anaconda](https://www.anaconda.com/data-science-platform), you can create a new environment `civrealm` with Python 3.8 by running the following command:
```bash
conda create -n civrealm python=3.8
```

## Docker Image of Freeciv-web
!!! warning "Do not use the original Freeciv-web" 
    Please do NOT use the image built based on the [original Freeciv-web repo](https://github.com/freeciv/freeciv-web). The image has been customize to suit agent training functionalities. The latest commits in that repo might cause compatibility issues.

CivRealm provides an interface for programmatic control of the Freeciv-web game. To test CivRealm locally (on <http://localhost>), please:

1. Download our customized docker image from [here](https://drive.google.com/file/d/1tf32JpwqGN7AtUPe0Q4fIRkE4icSM-51/view?usp=sharing).

2. Run the following command to load the docker image to use it locally:
```bash
docker load -i IMAGE_FILE_NAME
```

!!! note "Docker version"
    Please make sure you have installed **the latest** docker engine and docker-compose. Using older versions of docker may result in unexpected erorrs.
!!! tip "Docker permission"
    If the docker command complains about the sudo permission, please follow the instruction [here](https://askubuntu.com/questions/477551/how-can-i-use-docker-without-sudo).
