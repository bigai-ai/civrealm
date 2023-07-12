#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
docker cp "${SCRIPT_DIR}/game_save/testcontroller" freeciv-web:/var/lib/tomcat10/webapps/data/savegames/