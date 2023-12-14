import os
import subprocess

test_dir = os.path.dirname(__file__)
service_save_dir = "/var/lib/tomcat10/webapps/data/savegames/"
service_minitask_save_dir = os.path.join(service_save_dir, "minitask/")


def copy_test_game_save():
    """copy tests game_save to CI freeciv-web service"""
    save_dir = os.path.join(test_dir, "tests", "game_save")
    for username in next(os.walk(save_dir))[1]:
        subprocess.call(
            f"cp -rd {os.path.join(save_dir,username)} {service_save_dir}",
            shell=True,
            executable="/bin/bash",
        )


if __name__ == "__main__":
    copy_test_game_save()
