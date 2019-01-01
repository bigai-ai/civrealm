
from setuptools import setup, find_packages
from distutils.command.build import build
#from setuptools.command.build import build
import subprocess
import os

package_dirs = {"freecivbot": os.sep.join(['src','freecivbot']),
                "gym_freeciv_web": os.sep.join(["src", "gym_freeciv_web"]),
                "gym_freeciv_web.envs": os.sep.join(["src", "gym_freeciv_web", "envs"])}
package_list = list(package_dirs.keys())

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
      data_files = [('/usr/local/bin', ['civ_prep_selenium.sh'])],
      entry_points = {'console_scripts': ["build_freeciv_server=freecivbot.build_server:build_docker_img",
                                          "test_freeciv_web_gym=gym_freeciv_web.random_test:main"]},
      install_requires=['docker','urllib3', 'BitVector', 'numpy', 'tornado', 'gym', 'selenium', 'websocket-client'],
      zip_safe=False)
