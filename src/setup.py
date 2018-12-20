from setuptools import setup
import setuptools.command.build_py


class BuildContainerCommand(setuptools.command.build_py.build_py):
  """Custom build command."""

  def run(self):
    self.run_command('./build_server.sh')
    setuptools.command.build_py.build_py.run(self)

setup(name='freecivbot',
      version='0.1',
      description='Freeciv bot allowing for research on AI for complex strategy games',
      url='http://github.com/chris1869/freeciv-bot',
      author='Chris1869',
      author_email='TBD',
      license='GLP3.0',
      packages=['freecivbot'],
      install_requires=['docker'],
      cmdclass={'build_freeciv-web': BuildContainerCmd}
      zip_safe=False)
