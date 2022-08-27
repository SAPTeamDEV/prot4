import os

from . import utils
from . import settings_data
from . import data

class Settings(object):
	def _reset(self):
		for s in data.settingVals:
			setattr(settings_data, s, data.settingVals[s])
		self._write()

	def _write(self):
		if not havePermission or not data.settingsFileExists:
			return
		with open(data.settingsFilePath, 'w') as file:
			values = ''
			for s in dir(settings_data):
				if not s.startswith('_'):
					values += f'{s} = {getattr(settings_data, s)}\n'
			file.write(values)

	def __getattr__(self, key):
		if not key.startswith('_'):
			try:
				if key == 'reset':
					self._reset()
					utils.printMsg('settings restored to default values')
					return
				return getattr(settings_data, key)
			except KeyError:
				utils.printMsg('KeyError: ' + "'" + key + "'", color='red')
				return
		else:
			return object.__getattribute__(self, key)

	def __setattr__(self, key, val):
		if not key.startswith('_'):
			if not key in settingVals:
				utils.printErr('option is invalid')
				return
			if type(settingVals[key]) == list and not val in settingVals[key][1]:
				utils.printErr('value is invalid')
				return
			setattr(settings_data, key, val)
			self._write()
		else:
			object.__setattr__(self, key, val)

settings = Settings()

