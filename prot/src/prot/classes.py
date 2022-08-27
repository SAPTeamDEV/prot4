import threading
import time

from .database import register, query
from .converters import dict2matrix, list2str

class ProtObject(object):
	type = 'object'

	def __init__(self, *args, **kwargs):
		self.id = register('object', self)
		register('dataSlot', self.id)

	def __setattr__(self, name, value):
		if name in ['type', 'id', 'data'] and hasattr(self, name):
			raise AttributeError(f"can't change {name} attribute.")
		return super().__setattr__(name, value)

	def __repr__(self):
		return f'<{self.__class__.__name__} {self.type} at {self.id}>'

	def __str__(self):
		return f'<{self.__class__.__name__} {self.type} at {self.id}>'

	@property
	def data(self):
		return query('dataSlot', self.id)

class Matrix(list):
	def __getitem__(self, key):
		if type(key) == int:
			return super().__getitem__(key)
		else:
			res = self.get(key, default=Empty)
			if res == Empty:
				raise KeyError(repr(key))
			return res

	def __setitem__(self, key, value):
		self._checkValue(value)
		if type(key) == int:
			super().__setitem__(key, value)
		else:
			self.append([key, value])

	def __init__(self, value=[]):
		try:
			if value:
				self._checkValue(value)
		except:
			for v in value:
				self._checkValue(v)
		super().__init__(value)

	def _checkValue(self, value):
		if type(value) in [list, tuple, Matrix] and len(value) == 2:
			return True
		raise TypeError('value must be object of Matrix, list or tuple classes and should have only two members')

	def append(self, value):
		self._checkValue(value)
		super().append(value)

	def __delitem__(self, key):
		if type(key) == int:
			super().__delitem__(key)
		for k in self:
			try:
				if k[0] == key:
					self.remove(k)
			except: pass

	def get(self, key, default=None):
		for k in self:
			try:
				if k[0] == key:
					return k[1]
			except: pass
		return default

class LoopBack(object):
	def __init__(self, *args, **kwargs):
		pass

	def loop(*args, **kwargs):
		return self.loop

	def __getattribute__(self, key):
		try:
			return super().__getattribute__(key)
		except:
			return self.loop

class LockedDict(dict):
	def __delitem__(self, val):
		raise TypeError('dict is locked.')

	def __setitem__(self, key, val):
		raise TypeError('dict is locked.')

class Database(ProtObject):
	def __getattribute__(self, val):
		if str(val).startswith('_') or val in dir(self) or not 'dict' in dir(self):
			return super().__getattribute__(val)
		else:
			if not val in self.dict:
				return super().__getattribute__(val)
			return self.dict[val]

	def __setattr__(self, key, val):
		if str(key).startswith('_') or str(key) in ['type', 'id', 'data', 'append', 'add', 'remove', 'dict', 'list']:
			super().__setattr__(key, val)
		else:
			self.dict[key] = val

	def __delattr__(self, val):
		try:
			del self.dict[val]
		except:
			super().__delattr__(val)

	def __getitem__(self, val):
		return self.list[val] if type(val) == int else self.dict[val]

	def __setitem__(self, key, val):
		self.dict[key] = val

	def __delitem__(self, val):
		del self.dict[val]

	def __init__(self, update=None):
		super().__init__()
		self.dict = {} if not type(update) == dict else update
		self.list = [] if not type(update) == list else update

	def append(self, val):
		self.list.append(val)

	def add(self, val):
		if len(str(val).split(':')) == 1:
			self.list.append(val)
		else:
			self.dict[str(val).split(':')[0]] = str(val).split(':')[1]

	def remove(self, val):
		self.list.remove(val)

class OptionsDatabase(Database):
	def __getitem__(self, val):
		return self.dict[val]

	def __add__(self, other):
		if not type(other) == OptionsDatabase:
			raise TypeError(f'can only concatenate OptionsDatabase (not "{type(other).__name__}") to OptionsDatabase')
		newDict = {}
		for k in self.dict:
			newDict[k] = self.dict[k]
		for k in other.dict:
			newDict[k] = other.dict[k]
		return OptionsDatabase(newDict)

	def __init__(self, update=None, rules=None, allowExtraArgs=True):
		ProtObject.__init__(self)
		self.dict = {} if not type(update) == dict else update
		if rules:
			for i, o in enumerate(rules):
				if type(update) == tuple:
					try:
						if o.get('position', Empty) is Empty:
							self.dict[o['key']] = update[i]
						else:
							self.dict[o['key']] = update[o['position']]
					except:
						raise Exception(f"argument '{o['key']}' is required.")
				if not o['key'] in self.dict:
					if o.get('required', False):
						raise Exception(f"argument '{o['key']}' is required.")
					self.dict[o['key']] = o.get('default', None)
				if o.get('allowed', Empty) is not Empty:
					if not self.dict[o['key']] in (o['allowed'] if type(o['allowed']) == list else [o['allowed']]):
						raise Exception(f"value of argument '{o['key']}' is invalid.")
				if o.get('denied', Empty) is not Empty:
					if self.dict[o['key']] in (o['denied'] if type(o['denied']) == list else [o['denied']]):
						raise Exception(f"value of argument '{o['key']}' is invalid.")
				if o.get('type', Empty) is not Empty:
					if not type(self.dict[o['key']]) == o['type']:
						raise Exception(f"argument '{o['key']}' must be an {o['type'].__name__} object.")
				if o.get('call', Empty) is not Empty:
					o['call'](self.dict[o['key']])
				if o.get('update', Empty) is not Empty:
					self.dict[o['key']] = o['update'](self.dict[o['key']])

		if not allowExtraArgs:
			ruleKeys = [o['key'] for o in rules]
			for k in self.dict:
				if not k in ruleKeys:
					raise Exception(f"argument '{k}' not requested.")

class TextListFile(object):
	def __init__(self, filePath, newFile=None):
		self.file = open(filePath)
		self.rawdata = self.file.read()
		self.data = self.rawdata.splitlines()
		if newFile:
			self.newfile = open(newFile, 'w')
			self.mode = 'w'
		else:
			self.newfile = None
			self.mode = 'r'

	def optimize(self):
		new = []
		for s in self.data:
			if s in new or not s:
				continue
			else:
				new.append(s)
		self.data = new

	def commit(self):
		if self.mode == 'r':
			raise Exception("can't write in read mode.")
		self.newfile.write(list2str(self.data, '\n'))
		self.newfile.flush()

	def close(self):
		if self.mode == 'w':
			self.newfile.close()
		self.file.close()

class TextDictFile(object):
	def __init__(self, filePath, newFile=None, createFile=False):
		if createFile and not _os.path.exists(filePath):
			open(filePath, 'w').close()
			newFile = filePath
		self.file = open(filePath)
		self.rawdata = self.file.read()
		lines = self.rawdata.splitlines()
		if not self.checkFormat(lines):
			raise TypeError('file type not supported.')
		self.data = {}
		for l in lines:
			data = Database()
			for d, v in {'key':l.split(':')[0].strip(), 'val':l.split(':')[1].strip()}.items():
				try:
					if '.' in v:
						v = float(v)
					else:
						v = int(v)
				except:
					if v in ['True', 'False', 'None']:
						v = True if v == 'True' else False if v == 'False' else None
					else:
						v = str(v)
				setattr(data, d, v)
			self.data[data.key] = data.val
		if newFile:
			self.newfile = open(newFile, 'w')
			self.mode = 'w'
		else:
			self.newfile = None
			self.mode = 'r'

	def checkFormat(self, data):
		for d in data:
			if not d:
				continue
			if d.startswith('#'):
				continue
			if not ':' in d or not len(d.split(':')) == 2:
				return False
		return True

	def commit(self):
		if self.mode == 'r':
			raise Exception("can't write in read mode.")
		self.newfile.write(list2str(self.convert(), '\n'))
		self.newfile.flush()

	def convert(self, data=None):
		out = []
		if not data:
			data = self.data
		for d in data:
			out.append(str(d) + ' : ' + str(data[d]))
		return out

	def close(self):
		if self.mode == 'w' and not self.newfile.closed:
			self.newfile.close()
		if not self.file.closeed:
			self.file.close()

class TimerThread(threading.Thread):
	def __init__(self, id, time, call, repeat=False):
		threading.Thread.__init__(self)
		self.id = id
		self.time = time
		self.call = call
		self.repeat = repeat

	def run(self):
		run = True
		while run:
			if query('dataSlot', self.id).status == 'stopped':
				break
			time.sleep(self.time)
			if query('dataSlot', self.id).status == 'stopped':
				break
			if callable(self.call):
				self.call()
			if not self.repeat:
				run = False
		query('dataSlot', self.id).status = 'stopped'

class Timer(ProtObject):
	def __init__(self, time, call, repeat=False, type='background'):
		super().__init__()
		self.data.status = 'initializing'
		self.type = type
		if str(time)[-1] in ['s', 'm', 'h']:
			unit = str(time)[-1]
			time = float(str(time)[:-1])
			if unit in ['m', 'h']:
				time = time * 60
			if unit in ['h']:
				time = time * 60
		time = float(time)
		self.data.status = 'ready'
		self.time = time
		self.call = call
		self.repeat = repeat
		self.type = type
		if not self.type in ['background', 'foreground']:
			printErr('type is invalid')

	def start(self):
		self.data.status = 'started'
		self.thread = TimerThread(self.id, self.time, self.call, self.repeat)
		if self.type == 'background':
			self.thread.daemon = True
			self.thread.start()
		elif self.type == 'foreground':
			self.thread.run()

	def end(self):
		self.data.status = 'stopped'

	def __del__(self):
		self.end()

class Call(ProtObject):
	def __init__(self, *args, **keywds):
		super().__init__()
		self.call = args[0]
		self.args = args[1:]
		self.keywds = keywds

	def __call__(self, *argsExtra):
		return self.call(*self.args+argsExtra, **self.keywds)

class ProtString(str):
	def compile(self):
		try:
			if '.' in self:
				out = float(self)
			else:
				out = int(self)
		except:
			if self in ['True', 'False', 'None']:
				out = True if self == 'True' else False if self == 'False' else None
			else:
				out = str(self)
		return out

	@property
	def type(self):
		return self.split('.')[-1].lower()

	@property
	def has_type(self):
		return len(self.split('.')) > 1

	def extract(self):
		splittedList = self.split(',')
		splittedDict = {}
		splittedListNew = []
		for i in splittedList:
			if len(i.split(':')) > 1:
				splittedDict[i.split(':')[0]] = i.split(':')[1]
		for i in splittedList:
			if len(i.split(':')) > 1:
				for s in i.split(':'):
					splittedListNew.append(s)
			else:
				splittedListNew.append(i)
		if len(splittedListNew) == 0 and len(splittedDict) == 0:
			raise ValueError('this string is not encoded.')
		else:
			data = Database()
			for i in splittedListNew:
				data.append(i)
			for i in splittedDict:
				data[i] = splittedDict[i]
			return data

	def __setitem__(self, index, val):
		stringList = []
		for string in self:
			stringList.append(string)
		stringList[index] = str(val)
		compiledString = ''
		for string in stringList:
			compiledString += string
		self.query = self.__class__(compiledString)

	def __delitem__(self, key):
		stringList = []
		for string in self:
			stringList.append(string)
		del stringList[key]
		compiledString = ''
		for string in stringList:
			compiledString += string
		self.query = self.__class__(compiledString)

	def __div__(self, other):
		out = []
		try:
			if len(self) > other:
				splitDelay = len(self) // other
				tStr = str(self)
				for i in range(splitDelay):
					out.append(tStr[:other])
					tStr = tStr[other:]
				if not tStr == '':
					out.append(tStr)
			else:
				out = [self]
		except:
			out = []
		return out

Empty = LoopBack()
