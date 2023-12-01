# System Requirements

Civrealm requires Python version >=3.8.

In order to test the civrealm on <http://localhost>, please download the docker image from: https://drive.google.com/file/d/1tf32JpwqGN7AtUPe0Q4fIRkE4icSM-51/view?usp=sharing.

> :warning:
> Please make sure you have installed **the latest** docker engine and docker-compose.
> Using older versions of docker may result in unexpected erorrs.
> Please do NOT use the image built based on the Freeciv-web repo (https://github.com/freeciv/freeciv-web) because the latest commits in that repo will cause compatibility issues.

After downloading the docker image, please run the following command to load the image so that docker can use it locally:
```bash
docker load -i IMAGE_FILE_NAME
```

> If the docker command complains about the sudo permission, please follow the instruction in: https://askubuntu.com/questions/477551/how-can-i-use-docker-without-sudo.