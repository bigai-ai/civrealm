import glob
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


def download_minitask_save():
    """download and unzip minitask.zip save to CI freeciv-web service"""

    zip_dir = os.path.join(test_dir, "minigame.zip")
    fileid = "1MB28bFHQPl0-KOGPEIa9d33StrU-S6lp"
    download_command = f"wget --load-cookies /tmp/cookies.txt \"https://docs.google.com/uc?export=download&confirm=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate 'https://docs.google.com/uc?export=download&id={fileid}' -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1\n/p')&id={fileid}\" -O {zip_dir} && rm -rf /tmp/cookies.txt"
    # download zip

    # Download minigame.zip from google drive if not found in builds/$CI_PROJECT_PATH
    if os.path.isfile(zip_dir):
        print("Found minigame.zip!")
    else:
        print("Downloading minigame.zip...")
        subprocess.check_call(
            download_command,
            shell=True,
        )
        if not os.path.isfile(zip_dir):
            raise Exception(
                f"Failed to Download minigame.zip using download_command {download_command}"
            )
        print(f"Minigame downloaded to {zip_dir}.")

    local_path = "/tmp/minigame/"
    subprocess.check_call(f"unzip {zip_dir} -d {local_path}", shell=True)

    cwd = os.path.join(local_path, "minitask")
    print(f"Start unziping minitask saves")
    for minitask_zip in os.listdir(cwd):
        if not minitask_zip.endswith(".zip"):
            continue
        # copy zip
        subprocess.check_call(
            f"cp {os.path.join(cwd,minitask_zip)} {service_minitask_save_dir}",
            shell=True,
        )
        # unzip subfolder
        subprocess.check_call(
            f"unzip -o {os.path.join(service_minitask_save_dir,minitask_zip)} -d {service_minitask_save_dir}",
            shell=True,
        )
        subprocess.call(
            f"rm {os.path.join(service_minitask_save_dir,minitask_zip)}", shell=True
        )
    subprocess.check_call(
        f"touch {os.path.join(test_dir,'minitask_zipped.flag')}", shell=True
    )


if __name__ == "__main__":
    copy_test_game_save()
    download_minitask_save()
