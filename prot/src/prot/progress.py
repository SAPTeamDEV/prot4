import time

from . import color
from . import utils

from .classes import ProtObject

class Widget(ProtObject):
	type = 'Widget'
	def __init__(self, progressNeeded=False):
		super().__init__()
		self.progress = None
		self._finished = False
		self.progressNeeded = progressNeeded

	def _set_progress(self, progress):
		if not isinstance(progress, Progress):
			raise TypeError(str(progress)+' must be instance of '+str(Progress))
		self.progress = progress

	def _finish(self):
		self._finished = True

	def __call__(self):
		if self.progressNeeded and self.progress is None:
			raise Exception('progress instance needed.')

class TimeWidget(Widget):
	def __init__(self, milisec=False, min=True, hour=True):
		Widget.__init__(self)
		self.milisec = milisec
		self.min = min
		self.hour = hour
		self._startTime = time.time()
		self.startTime = int(self._startTime)

	def calc_time(self):
		_now = time.time()
		now = int(_now)
		string = ''
		if self.milisec:
			milisec = str(_now - self._startTime).split('.')[1][:3]
		sec = now - self.startTime
		min = 0
		hour = 0
		if sec >= 60 and self.min:
			for m in range(sec // 60):
				sec -= 60
				min += 1
		if min >= 60 and self.hour:
			for m in range(min // 60):
				min -= 60
				hour += 1
		if len(str(hour)) <= 1:
			hour = '0' + str(hour)
		if len(str(min)) <= 1:
			min = '0' + str(min)
		if len(str(sec)) <= 1:
			sec = '0' + str(sec)
		if self.hour:
			string += str(hour)+':'
		if self.min:
			string += str(min)+':'
		if self.milisec:
			sec = str(sec) + '.' + milisec
		string += str(sec)
		return string

	def __call__(self):
		Widget.__call__(self)
		return self.calc_time()

class BarWidget(Widget):
	def __init__(self, fill='█', empty='░', fillPerPercent=5, color=None):
		Widget.__init__(self, True)
		self.fill = fill
		self.empty = empty
		self.fpp = fillPerPercent
		self.color = color

	def __call__(self):
		Widget.__call__(self)
		return self.createBar()

	def createBar(self):
		perc = int(self.progress.calc_perc().split('.')[0])
		bar = ''
		filled = 0
		if perc >= self.fpp:
			for c in range(perc // self.fpp):
				bar += self.fill
				filled += 1
		for f in range(100//self.fpp-filled):
			bar += self.empty
		if self.color and color.verifyColor(self.color, False):
			bar = '-' + self.color + bar + '*end'

		return bar

class TaskWidget(Widget):
	def __init__(self, tasks={}):
		Widget.__init__(self, True)
		self.tasks = tasks
		self.percTasks = {}
		self.eventTasks = {}
		self.firstRun = True
		self.checkTasks()

	def checkTasks(self):
		for t in self.tasks:
			if t == 'perc':
				self.percTasks = self.tasks[t]
			elif t == 'event':
				self.eventTasks = self.tasks[t]

	def __call__(self):
		Widget.__call__(self)
		return calc_task()

	def calc_task(self):
		if self.eventTasks:
			if 'onFirstShow' in self.eventTasks and self.firstRun:
				self.firstRun = False
				return self.eventTasks['onFirstShow']
			if 'onFinish' in self.eventTasks and self._finished:
				return self.eventTasks['onFinish']
		if self.percTasks:
			perc = int(self.progress.calc_true_perc())
			for p in self.percTasks:
				if perc <= p:
					return self.percTasks[p]
		return ''

class CallWidget(Widget):
	def __init__(self, call, progressNeeded=False):
		Widget.__init__(self, progressNeeded)
		self.call = call

	def __call__(self):
		Widget.__call__(self)
		if self.progressNeeded:
			return self.call(self.progress)
		else:
			return self.call()

class ValueWidget(Widget):
	def __init__(self, value):
		Widget.__init__(self)
		self.value = value

	def __call__(self):
		Widget.__call__(self)
		return self.value

class LoadingWidget(Widget):
	def __init__(self, type='default'):
		Widget.__init__(self)
		self.type = type
		self.index = 0
		self.msg = None
		self.loadingType = None
		self.handleType()

	def handleType(self):
		typeData = self.getTypes()[self.type]
		self.msg = typeData['data']
		self.loadingType = type(typeData['data'])
		if self.loadingType == str:
			self.msg = ProtString(self.msg)

	def createMsg(self):
		if self._finished:
			return 'done'
		if self.loadingType == list:
			msg = self.msg[self.index]
			if self.index + 1 == len(self.msg):
				self.index = 0
			else:
				self.index += 1
			return msg
		else:
			msg = self.msg
			end = self.msg[-1]
			del self.msg[-1]
			self.msg = self.msg.query
			self.msg = ProtString(end + str(self.msg))
			return msg

	def __call__(self):
		Widget.__call__(self)
		return self.createMsg()

	def getTypes(self):
		return {
				'default':{
						'data':['|', '-']
						},
				'bar':{
						'data':'█████               '
						},
				'smallbar':{
						'data':'███         '
						},
				'verysmallbar':{
						'data':'██      '
						}
				}

class Progress(ProtObject):
	_deafultForm = '($VAL/$MAX) $PERC% $MSG'

	def __init__(self, val=0, minVal=0, maxVal=100, msg='completed', msgForm=None, replaces=[], color=None, inline=False):
		super().__init__()
		self._finished = False
		self.val = val
		self.min = minVal
		self.max = maxVal
		self.msg = msg
		self.inline = inline if utils.color.colorize() else False
		self.color = color
		if self.color:
			utils.color.verifyColor(self.color)
		if not msgForm:
			self.msgForm = self.get_default_form()
		else:
			self.msgForm = msgForm
		if replaces:
			for r in replaces:
				if not isinstance(r[1], Widget):
					raise TypeError(str(r[1])+' must be instance of Widget')
				r[1]._set_progress(self)
			self.extraReplaces = replaces
		else:
			self.extraReplaces = []
		self.show()

	def show(self):
		replaces = self.getDefaultReplaces()
		msg = self.do_replace(replaces)
		if self.inline:
			self.printInline(msg, self.color)
		else:
			utils.printMsg(msg, self.color)

	def getDefaultReplaces(self):
		return [
					['$VAL', self.val],
					['$MIN', self.min],
					['$MAX', self.max],
					['$PERC', self.calc_perc()],
					['$TRUE_PERC', self.calc_true_perc()],
					['$MSG', self.msg]
					]

	def clear(self):
		utils.printMsg('*clearline', end='', prefix=False)

	def printInline(self, msg, color=None):
		self.clear()
		utils.printMsg(msg, color, end='')

	def write(self, msg=''):
		if self.inline:
			utils.printMsg('\n' + msg)
		else:
			utils.printMsg(msg)

	def newline(self):
		if self.inline:
			utils.printMsg('', prefix=False)

	def finish(self):
		for r in self.extraReplaces:
			r[1]._finish()
		self._finished = True
		self.newline()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.finish()

	def get_default_form(self):
		return self._deafultForm

	def calc_perc(self):
		perc = str(100/self.max*self.val).split('.')
		perc[1] = perc[1][:3]
		return perc[0]+'.'+perc[1]

	def calc_true_perc(self):
		perc = str(100/self.max*self.val).split('.')[0]
		return perc

	def do_replace(self, replaces):
		tries = 0
		msg = self.msgForm
		while tries < 3 and '$' in msg:
			tries += 1
			for r in replaces:
				msg = msg.replace(r[0], str(r[1]))
			for r in self.extraReplaces:
				msg = msg.replace(r[0], str(r[1]()))
		return msg

	def update(self, val):
		self.val = max(self.min, min(self.max, val))
		self.show()

	def next(self, val=1):
		self.val = max(self.min, min(self.max, self.val + val))
		self.show()

class ProgressBar(Progress, BarWidget):
	def __init__(self, val=0, minVal=0, maxVal=100, msg='completed', msgForm=None, replaces=[], color=None, inline=False, fill='█', empty='░', fillPerPercent=5):
		BarWidget.__init__(self, fill=fill, empty=empty, fillPerPercent=fillPerPercent)
		Progress.__init__(self, val=val, minVal=minVal, maxVal=maxVal, msg=msg, msgForm=msgForm, replaces=replaces, color=color, inline=inline)
		self.progress = self

	def __repr__(self):
		return Progress.__repr__(self)

	def getDefaultReplaces(self):
		Progress.getDefaultReplaces(self) + [['$BAR', self()]]

	def finish(self):
		self._finish()
		Progress.finish(self)
