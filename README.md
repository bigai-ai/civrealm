# *CivRealm*: A Learning and Reasoning Odyssey in *Civilization* for Decision-Making Agents

[![Documentation Status](https://readthedocs.org/projects/openreview-py/badge/?version=latest)](<http://civilization.pages.mybigai.ac.cn/civrealm>)

CivRealm is an interactive environment for the open-source strategy game [Freeciv-web](https://github.com/freeciv/freeciv-web) based on [Freeciv](https://www.freeciv.org/), a Civilization-inspired game. Within CivRealm, we provide interfaces for two typical agent types: tensor-based reinforcement learning agents based on the [Gymnasium](https://gymnasium.farama.org/) API, and language-based agents powered by language models.

We also provide a set of tools for training and evaluating agents, as well as a set of baselines for both agent type. We hope that CivRealm can serve as a testbed for developing and evaluating agents that can learn and reason in complex environments.

![Punic War](docs/assets/punic_war_base.jpg)

## About

CivRealm is a fork of [freeciv-bot](https://github.com/chris1869/freeciv-bot) that was initiated several years ago and further developed by [BIGAI](https://www.bigai.ai/). Going forward, CivRealm will be maintained in the long term.

## Prerequisites

In order to test the civrealm on <http://localhost>, kindly follow the docker installation instructions on <https://gitlab.mybigai.ac.cn/civilization/freeciv-web.git>.

> :warning:
> Please make sure you have installed **the latest** docker engine and docker-compose.
> Using older versions of docker may result in unexpected errors.

## Installation

Installation for civrealm developers

```bash
cd civrealm
pip install -e .
```

<!-- 
### Update the freeciv-web image

Start the freeciv-web docker:

```bash
cd freeciv-web
docker compose up -d
```

Activate the civrealm virtual environment, and update the freeciv-web image:

```bash
update_freeciv_web_docker
```

Restart the freeciv-web container so that the change takes effect

```bash
cd freeciv-web
docker compose down
docker compose up -d
```
-->

### Testing the installation

To test if the installation is successful, run

```bash
test_civrealm 
```

To test with multiple players, run

```bash
test_civrealm --minp=2 --username=myagent
```

Then in another terminal, run

```bash
test_civrealm --username=myagent1
```

<!-- ### Using a different freeciv version

As a standard, the official docker image from the [official repository](https://github.com/freeciv/freeciv-web) will be pulled. If you want to create a custom freeciv server (e.g., different rulesets, customizations, etc.) you can use `build_freeciv_server` to create a custom docker image or run a separate image in parallel. In this case, you might need to adapt src/init_server.py -->


## Trouble shooting

The following are some common issues that you may encounter when running the code. If you encounter any other issues, please feel free to open an issue.

* If firefox keeps loading the page, please try to add the following line to `/etc/hosts`:

    ```bash
    127.0.0.1 maxcdn.bootstrapcdn.com
    127.0.0.1 cdn.webglstats.com
    ```

* If you encounter the following error when running `sudo civ_prep_selenium.sh`, please try [this solution](https://unix.stackexchange.com/questions/724518/the-following-packages-have-unmet-dependencies-containerd-io).

    ```bash
    ...
    The following packages have unmet dependencies:
    containerd.io : Conflicts: containerd
                    Conflicts: runc
    ...
    ```

* If you see the following error when running `test_civrealm`,  please see [this solution](https://stackoverflow.com/questions/72405117/selenium-geckodriver-profile-missing-your-firefox-profile-cannot-be-loaded). If this does not solve the problem, please check `geckodriver.log` for more information.

    ```bash
    selenium.common.exceptions.WebDriverException: Message: Process unexpectedly closed with status 1
    ```

    One potential solution on Ubuntu 22.04 is:

    ```bash
    sudo apt install firefox-geckodriver
    ln -s /snap/bin/firefox.geckodriver geckodriver
    ```

* If you see the following error when setting `take_screenshot: True`, it is caused by snap version of Firefox. Please try [System Firefox installation](https://support.mozilla.org/en-US/kb/install-firefox-linux#w_install-firefox-from-mozilla-builds-for-advanced-users).

  ```bash
  Your Firefox profile cannot be loaded. 
  It may be missing or inaccessible.
  ```

* If the screenshot is not centered on the location of your first unit, it is because you are using multiple displays. Please ensure the Firefox browser for screenshot pops up on your primary display.

