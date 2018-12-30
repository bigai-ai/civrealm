
from setuptools import setup, find_packages
from distutils.command.build import build
#from setuptools.command.build import build
import subprocess
import os

"""
#! To be reworked - currently no output via pip - shifting to manual install
class CustomInstallCommand(build):
    def run(self):
        #subprocess.call(["python", "src/freecivbot/build_server.py"])
        #os.system("python src/freecivbot/build_server.py")
        proc = subprocess.Popen(["python","-u", "src/freecivbot/build_server.py"], stdout=subprocess.PIPE)

        while True:
            line = proc.stdout.readline()
            if line != '':
                print line
            else:
                break
        build.run(self)
"""
import os

os.system("./prep_fire_selenium.sh")

package_dirs = {"freecivbot": os.sep.join(['src','freecivbot']),
                "gym_freeciv_web": os.sep.join(["src", "gym_freeciv_web"]),
                "gym_freeciv_web.envs": os.sep.join(["src", "gym_freeciv_web", "envs"])}
package_list = package_dirs.keys()

for item in ["bot", "connectivity", "city", "units", "game", "map", "players", "research", "utils"]:
    package_list.append("freecivbot."+item)
    package_dirs["freecivbot."+item] = os.sep.join([package_dirs["freecivbot"], item])

setup(name='freecivbot',
      version='0.1',
      description='Freeciv bot allowing for research on AI for complex strategy games',
      url='http://github.com/chris1869/freeciv-bot',
      author='Chris1869',
      author_email='TBD',
      license='GLP3.0',
      package_dir=package_dirs,
      packages=package_list,
      entry_points = {'console_scripts': ["build_freeciv_server=freecivbot.build_server:build_docker_img",
                                          "test_freeciv_web_gym=gym_freeciv_web.random_test:main"]},
      install_requires=['docker','urllib3', 'BitVector', 'numpy', 'tornado', 'gym', 'selenium', 'websocket'],
      zip_safe=False)
