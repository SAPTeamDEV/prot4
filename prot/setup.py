import os

from setuptools import setup, find_packages

from protbuilder import *

parent = 'src'
name, dir = findProt(parent)
version = getVersion(dir)
metadata = getMetadata(dir)
#description, content = parseReadme()
requirements = parseRequirements()
scripts = compileEntryPoints('scripts', dict(name=name, module=f'{name}.cli', function='main'))

parser = getParser(os.path.relpath(__file__), Database(globals()))
options = parser.parse_args(namespace=Database())
processOptions(options, Database(globals()))

setup(
	name=name, version=version.version, **metadata,
	#long_description=description, long_description_content_type=content,
	packages=find_packages(where="src"), package_dir={"": "src"}, zip_safe=False,
	entry_points=scripts, install_requires=requirements)