import os
import subprocess


def copy_test_game_save():

    if os.environ.get("CIVREALM_TEST_SAVE_DIR"):
        SAVE_DIR = os.environ["CIVREALM_TEST_SAVE_DIR"]
        print(f"Using game_save dir specified by SAVE_DIR: {SAVE_DIR}")
    else:
        SAVE_DIR = "/builds/civilization/civrealm/tests/game_save"
        print(f"SAVE_DIR not found, using default game_save dir: {SAVE_DIR}")

    for username in next(os.walk(SAVE_DIR))[1]:
        subprocess.call(
            f"cp -rd {SAVE_DIR}/{username} /var/lib/tomcat10/webapps/data/savegames/",
            shell=True,
            executable="/bin/bash",
        )


if __name__ == "__main__":
    copy_test_game_save()
