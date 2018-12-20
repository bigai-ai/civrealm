from setuptools import setup
from setuptools.command.install import install
import subprocess

class CustomInstallCommand(install):
    """Customized setuptools install command - prints a friendly greeting."""
    def run(self):
        subprocess.call(["python", "src/freecivbot/build_server.py"])
        install.run(self)

setup(name='freecivbot',
      version='0.1',
      description='Freeciv bot allowing for research on AI for complex strategy games',
      url='http://github.com/chris1869/freeciv-bot',
      author='Chris1869',
      author_email='TBD',
      license='GLP3.0',
      package_dir={'':'src'},
      packages=['freecivbot'],
      cmdclass={
                 'install': CustomInstallCommand,
                },
      install_requires=['docker'],
      zip_safe=False)
