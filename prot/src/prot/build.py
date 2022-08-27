import os
import shutil

from . import parsers
from . import session

from .classes import Database, ProtString
from .converters import list2str, pyCompile
from .exceptions import PackageNotFoundError
from .data import contentTypes, getStatus
from .utils import makeTree, getVarFromFile

status = Database(getStatus())

class VersionString(str):
	def __init__(self, *args, **kwargs):
		str.__init__(self)
		try:
			ver = self.split('.')
			try:
				self.major = int(ver[0])
			except:
				self.major = None
			try:
				self.minor = int(ver[1])
			except:
				self.minor = None
			try:
				self.micro = int(ver[2])
			except:
				self.micro = None
		except: pass

	def __str__(self):
		return self.version

	def __repr__(self):
		return self.version

	def __int__(self):
		return int(self.versionCode)

	def __eq__(self, other):
		other = type(self)(other)
		return int(self.versionCode).__eq__(int(other.versionCode))

	def __ne__(self, other):
		other = type(self)(other)
		return int(self.versionCode).__ne__(int(other.versionCode))

	def __ge__(self, other):
		other = type(self)(other)
		return int(self.versionCode).__ge__(int(other.versionCode))

	def __gt__(self, other):
		other = type(self)(other)
		return int(self.versionCode).__gt__(int(other.versionCode))

	def __le__(self, other):
		other = type(self)(other)
		return int(self.versionCode).__le__(int(other.versionCode))

	def __lt__(self, other):
		other = type(self)(other)
		return int(self.versionCode).__lt__(int(other.versionCode))

	def upgrade(self, target='default', maxMinor=9, maxMicro=9):
		if target == 'default':
			if self.micro is not None:
				target = 'micro'
			elif self.minor is not None:
				target = 'minor'
			elif self.major is not None:
				target = 'major'
		if self.micro is not None and self.micro >= maxMicro:
			minor = True
		else:
			minor = False
		if self.minor is not None and self.minor >= maxMinor:
			major = True
		else:
			major = False
		if False:
			print(f'target: {str(target)}')
			print(f'self.micro: {str(self.micro)}')
			print(f'maxMicro: {str(maxMicro)}')
			print(f'self.minor: {str(self.minor)}')
			print(f'maxMinor: {str(maxMinor)}')
			print(f'minor: {str(minor)}')
			print(f'self.major: {str(self.major)}')
			print(f'major: {str(major)}')
		if self.micro is not None and target == 'micro':
			self.micro += 1
		if self.minor is not None and (target == 'minor' or minor) and not major:
			if self.micro is not None:
				self.micro = 0
			self.minor += 1
		if self.major is not None and (target == 'major' or (major and minor)):
			if self.micro is not None:
				self.micro = 0
			if self.minor is not None:
				self.minor = 0
			self.major += 1
		return self.compile()

	def compile(self):
		ver = []
		if self.major is not None:
			ver.append(str(self.major))
		if self.minor is not None:
			ver.append(str(self.minor))
		if self.micro is not None:
			ver.append(str(self.micro))
		return '.'.join(ver)

	@property
	def version(self):
		return self.compile()

	@property
	def versionCode(self):
		versionCode = list2str(self.version.split('.'))
		versionCode += '0' * (3 - len(versionCode))
		return versionCode

def minVer(*args):
	if len(args) == 1:
		args = args[0]
	if args and type(args) in [list, tuple]:
		args = [VersionString(arg) for arg in args]
		value = args[0]
		for v in args[1:]:
			if v < value:
				value = v
	return value

def maxVer(*args):
	if len(args) == 1:
		args = args[0]
	if args and type(args) in [list, tuple]:
		args = [VersionString(arg) for arg in args]
		value = args[0]
		for v in args[1:]:
			if v > value:
				value = v
	return value

def getParser(name, globals):
	parsers.registerProgramName(name, 'builder')

	parser = parsers.ProtBuilderArgumentParser(
                            prog=name,
                            description=f'build {globals.name} with {status.name}.',
							allow_argv=True,
							remove_args=True,
							help_on_none=True
                            )

	parser.add_argument('-u', '--upgrade', action='upgrade', globals=globals)

	parser.add_argument(f'--update-builder', action='store_true', dest='update',
						 help=f'update {status.name} with {globals.name} installer')

	parser.add_argument('argv', nargs='...', metavar='setup args',
						help='setup arguments, you can see usages with --help-commands')

	return parser

def processOptions(options, globals):
	if options.update:
		print(f'updating {status.name} with {globals.name} {globals.version}')
		updateBuilder(globals)

def updateBuilder(globals):
	shutil.rmtree(status.dir)
	shutil.copytree(globals.dir, status.dir)
	shutil.rmtree(os.path.join(status.dir, 'bs'))
	shutil.rmtree(os.path.join(status.dir, 'pip'))
	pyCompile(status.dir, False, True, True)

def parseRequirements(file='requirements.txt'):
	with open(file) as file:
		return file.read().splitlines()

def findProt(source='.'):
	for name in os.listdir(source):
		dir = os.path.join(source, name)
		if 'build_metadata.py' in os.listdir(dir):
			return name, dir
	raise PackageNotFoundError('prot')

def getVersion(source='.'):
	path = os.path.join(source, '__version__.py')
	version = getVarFromFile(path, '__version__')
	return VersionString(version)

def getMetadata(source='.'):
	path = os.path.join(source, 'build_metadata.py')
	metadata = getVarFromFile(path, 'metadata', True)
	return metadata

def compileEntryPoints(type, *args):
	if type == 'scripts':
		type = 'console_scripts'
	entryPoints = {}
	entryPoints[type] = []
	for arg in args:
		if not isinstance(arg, Database):
			arg = Database(arg)
		entryPoints[type] += [f'{arg.name}={arg.module}:{arg.function}']
	return entryPoints

def parseReadme(file='README.md'):
	file = ProtString(file)
	type = file.type
	if not type in contentTypes:
		type = 'rst'
	with open(file) as file:
		readme = file.read()
	return readme, contentTypes[type]
