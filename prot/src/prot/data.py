import sys
import os
import io

from .ansitowin32 import AnsiToWin32
from . import color
from .__version__ import __version__ as version

Fore = color.AnsiFore()
Back = color.AnsiBack()
Style = color.AnsiStyle()
Cursor = color.AnsiCursor()
clear_line = color.clear_line
clear_screen = color.clear_screen

slots = {
		'dataSlot': [
					'programNames',
					'treeCache',
					'treeCache.dict',
					'treeCache.dict.cache',
					'treeCache.dict.attrs',
					'treeCache.list',
					'treeCache.list.cache',
					'treeCache.list.attrs'
					]
		}

dataStore = None

if os.name == 'nt':
	Win32Adapter = AnsiToWin32(sys.stdout, convert=True)
else:
	Win32Adapter = None

haveWin32Adapter = isinstance(Win32Adapter, AnsiToWin32)
haveColor = not os.name == 'nt' or haveWin32Adapter

def getWin32AdapterStatus():
	global haveWin32Adapter
	if isinstance(Win32Adapter, AnsiToWin32) and type(Win32Adapter.wrapped) == io.TextIOWrapper and Win32Adapter.wrapped == sys.stdout:
		haveWin32Adapter = True
	else:
		haveWin32Adapter = False
	return haveWin32Adapter

def getColorStatus():
	global haveColor
	if not os.name == 'nt' or getWin32AdapterStatus():
		haveColor = True
	else:
		haveColor = False
	return haveColor

def getOutput():
	if os.name == 'nt' and getColorStatus():
		return Win32Adapter
	else:
		return sys.stdout

def getStatus():
	status = {}
	status['dir'] = dir
	status['parent'] = parent
	status['name'] = name
	status['version'] = version
	status['hasPip'] = hasPip
	status['havePermission'] = havePermission
	status['official'] = official
	status['unofficial'] = unofficial
	status['builder'] = builder
	status['light'] = status['internalUse'] = light
	return status

dir = os.path.dirname(__file__)
parent, name = os.path.split(dir)
hasPip = os.path.isdir(os.path.join(dir, 'pip'))
official = name == 'prot'
unofficial = not official
builder = name == 'protbuilder'
light = internalUse = name == 'lightprot'

getColorStatus()

settingsFilePath = os.path.join(os.path.dirname(__file__), 'settings_data.py')
settingsFileExists = os.path.exists(settingsFilePath)

try:
	_file = open(os.path.join(os.path.dirname(__file__), 'test'), 'w')
	_file.close()
	del _file
	os.remove(os.path.join(os.path.dirname(__file__), 'test'))
	havePermission = True
except PermissionError:
	havePermission = False

contentTypes = {
				'txt': 'text/plain',
				'rst': 'text/x-rst',
				'md': 'text/markdown',
				}

registeredDatabaseTypes = {}

colors = {
			'foreground': {
							'black':Fore.BLACK,
							'red':Fore.RED,
							'green':Fore.GREEN,
							'yellow':Fore.YELLOW,
							'blue':Fore.BLUE,
							'magenta':Fore.MAGENTA,
							'cyan':Fore.CYAN,
							'white':Fore.WHITE,
							'reset':Fore.RESET
							},
			'background': {
							'black':Back.BLACK,
							'red':Back.RED,
							'green':Back.GREEN,
							'yellow':Back.YELLOW,
							'blue':Back.BLUE,
							'magenta':Back.MAGENTA,
							'cyan':Back.CYAN,
							'white':Back.WHITE,
							'reset':Back.RESET
							},
			'style': {
						'bright':Style.BRIGHT,
						'dim':Style.DIM,
						'normal':Style.NORMAL,
						'end':Style.RESET_ALL,
						'clearline':'\r\x1b[K',
						'clear':clear_screen(),
						}
		}

colorSymbols = {'foreground':'-', 'background':'+', 'style':'*'}

charDict = {
				'lowers' : 'abcdefghijklmnopqrstuvwxyz',
				'uppers' : 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
				'symbols' : './~!@#$%&*-,_=+?',
				'numbers' : '0123456789'
				}

patterns = [
			'%s =',
			'%s=',
			'as %s',
			'import %s',
			'%s,'
			]

settingVals = {
				'localRepository':'default',
				'orderedBuiltinList':[False, [False, True]],
				'ui':['normal', ['verysmall', 'small', 'normal']],
				'colorize':[True, [False, True]],
				'prefix':None,
				'color':[None, [color for color in colors['foreground']] + [None]]
				}