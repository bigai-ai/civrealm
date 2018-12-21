
from setuptools import setup
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
setup(name='freecivbot',
      version='0.1',
      description='Freeciv bot allowing for research on AI for complex strategy games',
      url='http://github.com/chris1869/freeciv-bot',
      author='Chris1869',
      author_email='TBD',
      license='GLP3.0',
      package_dir={'':'src'},
      packages=['freecivbot', 'gym_freeciv_web' ],
      entry_points = {'console_scripts': ["build_freeciv_server=freecivbot.build_server:build_docker_img"]},
      install_requires=['docker','urllib', 'BitVector', 'numpy', 'tornado', 'gym'],
      zip_safe=False)
