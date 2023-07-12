import os
import subprocess


test_dir = os.path.dirname(__file__)
subprocess.call(
    f'docker cp {test_dir}/game_save/testcontroller freeciv-web:/var/lib/tomcat10/webapps/data/savegames/',
    shell=True, executable='/bin/bash')
