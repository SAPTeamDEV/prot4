import hashlib
import random
import runpy
import os
import sys

from . import color
from . import database
from . import data
from . import settings
from . import win32

def printMsg(msg='', color=None, end='\n', file=None, colorize=True, prefix=True):
	if prefix and settings.settings.prefix:
		msg = settings.settings.prefix + msg
	if colorize:
		color = color if not settings.settings.color else settings.settings.color
		if color and data.color.verify(color, 'foreground'):
			msg = '-' + color + msg + '*end'
		msg = data.color.process(msg)
	file = file if file else data.getOutput()
	file.write(msg + end)
	file.flush()

def printErr(msg):
	printMsg('ERROR: ' + str(msg), color='red')

def printWarn(msg):
	printMsg('WARNING: ' + str(msg), color='yellow')

def makeTree(source='.', type='list', extentions=[], subfolders=False, ignoreCache=False, updateCache=False, ignoreExceptions=False):
    if not updateCache and not ignoreCache and source in database.query('dataSlot', 'treeCache')[type]['cache'] and database.query('dataSlot', 'treeCache')[type]['attrs'][source] == (subfolders, ignoreExceptions):
        return database.query('dataSlot', 'treeCache')[type]['cache'][source]
    try:
        if type=='dict':
            tree = {}
            for p in os.listdir(source):
                if os.path.isdir(os.path.join(source, p)) and subfolders:
                    for name, path in makeTree(os.path.join(source, p), type, extentions, subfolders, ignoreCache,updateCache, ignoreExceptions).items():
                        tree[name] = path
                else:
                    tree[p] = os.path.join(source, p)
                    if extentions and not p.split('.')[-1].lower() in extentions:
                        del tree[p]
        else:
            tree = []
            for p in os.listdir(source):
                if os.path.isdir(os.path.join(source, p)) and subfolders:
                    tree += makeTree(os.path.join(source, p), type, extentions, subfolders, ignoreCache, updateCache, ignoreExceptions)
                else:
                    tree.append(os.path.join(source, p))
                    if extentions and not p.split('.')[-1].lower() in extentions:
                        tree.remove(os.path.join(source, p))
    except:
        if not ignoreExceptions:
            raise

    if not ignoreCache:
        database.query('dataSlot', 'treeCache')[type]['cache'][source] = tree
        database.query('dataSlot', 'treeCache')[type]['attrs'][source] = (subfolders, ignoreExceptions)
    return tree

def getRandomString(Len=4, types=['lowers', 'uppers', 'symbols', 'numbers']):
	if not type(types) == list:
		raise TypeError('types argument must be a list object.')
	string = ''
	for r in range(Len):
		string += random.choice(list(data.charDict[random.choice(types)]))
	return string

def lister(obj):
    if type(obj) == list:
        return obj
    elif type(obj) in [tuple, dict]:
        return list(obj)
    else:
        return [obj]

def testSpeed(count):
    from .progress import Progress, TimeWidget
    progress = Progress(maxVal=count, msgForm='($VAL/$MAX) $TIME $PERC% completed', replaces=[['$TIME', TimeWidget(milisec=True)]], inline=True)
    for c in range(count):
        progress.next()
    progress.newline()

def getVarFromFile(file, variable, runEntireFile=False):
    if type(file) == str:
        file = open(file)
    file = file.read()
    if not runEntireFile:
        fileMap = file.splitlines()
        for f in fileMap:
            if f:
                for p in data.patterns:
                    cp = p % variable
                    if cp in f:
                        class tempCls:
                            exec(f)
                        res = getattr(tempCls, variable)
                        return res
    else:
        class tempCls:
            exec(file)
        res = getattr(tempCls, variable)
        return res

def checkMethods(obj):
	for s in dir(obj):
		printMsg(s+' : '+str(getattr(obj, s)))

def callMethods(obj):
	for s in dir(obj):
		try:
			printMsg('result of '+s+'() is '+str(getattr(obj, s)()))
		except:
			printMsg('error in '+str(s)+'()')

def callMethodsWithArg(obj, arg):
	for s in dir(obj):
		try:
			printMsg('result of '+s+'('+str(arg)+') is '+str(getattr(obj, s)(arg)))
		except:
			printMsg('error in '+str(s)+'('+str(arg)+')')

def checkFileSame(file1, file2):
	try:
		md5s = [hashlib.md5(), hashlib.md5()]
		fs = [file1, file2]
		for i in range(2):
			f = open(fs[i], 'rb')
			block_size = 2 ** 20
			while True:
				data = f.read(block_size)
				if not data: break
				md5s[i].update(data)
			f.close()
			md5s[i] = md5s[i].hexdigest()
		return md5s[0] == md5s[1]
	except:
		return False

def condition(string):
	exec('res = '+string)
	return res

def runAsMain(args=None):
    if type(args) == list:
        pass
    elif type(args) == str:
        args = args.split(' ')
    else:
        args = sys.argv
    backup = sys.argv
    sys.argv = args
    runpy._run_module_as_main(sys.argv[0])
    sys.argv = backup

class WinTerm(object):
    def __init__(self):
        self._default = win32.GetConsoleScreenBufferInfo(win32.STDOUT).wAttributes
        self.set_attrs(self._default)
        self._default_fore = self._fore
        self._default_back = self._back
        self._default_style = self._style
        self._light = 0

    def get_attrs(self):
        return self._fore + self._back * 16 + (self._style | self._light)

    def set_attrs(self, value):
        self._fore = value & 7
        self._back = (value >> 4) & 7
        self._style = value & (color.WinStyle.BRIGHT | color.WinStyle.BRIGHT_BACKGROUND)

    def reset_all(self, on_stderr=None):
        self.set_attrs(self._default)
        self.set_console(attrs=self._default)
        self._light = 0

    def fore(self, fore=None, light=False, on_stderr=False):
        if fore is None:
            fore = self._default_fore
        self._fore = fore
        if light:
            self._light |= color.WinStyle.BRIGHT
        else:
            self._light &= ~color.WinStyle.BRIGHT
        self.set_console(on_stderr=on_stderr)

    def back(self, back=None, light=False, on_stderr=False):
        if back is None:
            back = self._default_back
        self._back = back
        if light:
            self._light |= color.WinStyle.BRIGHT_BACKGROUND
        else:
            self._light &= ~color.WinStyle.BRIGHT_BACKGROUND
        self.set_console(on_stderr=on_stderr)

    def style(self, style=None, on_stderr=False):
        if style is None:
            style = self._default_style
        self._style = style
        self.set_console(on_stderr=on_stderr)

    def set_console(self, attrs=None, on_stderr=False):
        if attrs is None:
            attrs = self.get_attrs()
        handle = win32.STDOUT
        if on_stderr:
            handle = win32.STDERR
        win32.SetConsoleTextAttribute(handle, attrs)

    def get_position(self, handle):
        position = win32.GetConsoleScreenBufferInfo(handle).dwCursorPosition
        position.X += 1
        position.Y += 1
        return position

    def set_cursor_position(self, position=None, on_stderr=False):
        if position is None:
            return
        handle = win32.STDOUT
        if on_stderr:
            handle = win32.STDERR
        win32.SetConsoleCursorPosition(handle, position)

    def cursor_adjust(self, x, y, on_stderr=False):
        handle = win32.STDOUT
        if on_stderr:
            handle = win32.STDERR
        position = self.get_position(handle)
        adjusted_position = (position.Y + y, position.X + x)
        win32.SetConsoleCursorPosition(handle, adjusted_position, adjust=False)

    def erase_screen(self, mode=0, on_stderr=False):
        handle = win32.STDOUT
        if on_stderr:
            handle = win32.STDERR
        csbi = win32.GetConsoleScreenBufferInfo(handle)
        cells_in_screen = csbi.dwSize.X * csbi.dwSize.Y
        cells_before_cursor = csbi.dwSize.X * csbi.dwCursorPosition.Y + csbi.dwCursorPosition.X
        if mode == 0:
            from_coord = csbi.dwCursorPosition
            cells_to_erase = cells_in_screen - cells_before_cursor
        elif mode == 1:
            from_coord = win32.COORD(0, 0)
            cells_to_erase = cells_before_cursor
        elif mode == 2:
            from_coord = win32.COORD(0, 0)
            cells_to_erase = cells_in_screen
        else:
            return
        win32.FillConsoleOutputCharacter(handle, ' ', cells_to_erase, from_coord)
        win32.FillConsoleOutputAttribute(handle, self.get_attrs(), cells_to_erase, from_coord)
        if mode == 2:
            win32.SetConsoleCursorPosition(handle, (1, 1))

    def erase_line(self, mode=0, on_stderr=False):
        handle = win32.STDOUT
        if on_stderr:
            handle = win32.STDERR
        csbi = win32.GetConsoleScreenBufferInfo(handle)
        if mode == 0:
            from_coord = csbi.dwCursorPosition
            cells_to_erase = csbi.dwSize.X - csbi.dwCursorPosition.X
        elif mode == 1:
            from_coord = win32.COORD(0, csbi.dwCursorPosition.Y)
            cells_to_erase = csbi.dwCursorPosition.X
        elif mode == 2:
            from_coord = win32.COORD(0, csbi.dwCursorPosition.Y)
            cells_to_erase = csbi.dwSize.X
        else:
            return
        win32.FillConsoleOutputCharacter(handle, ' ', cells_to_erase, from_coord)
        win32.FillConsoleOutputAttribute(handle, self.get_attrs(), cells_to_erase, from_coord)

    def set_title(self, title):
        win32.SetConsoleTitle(title)
