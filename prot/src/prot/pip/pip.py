import sys
import os
from .. import *

from ..settings import settings

def main(action, **values):
	rules = [
			{'key':'local',
			'default':False},
			{'key':'smart',
			'default':False},
			{'key':'value',
			'default':None},
			{'key':'export',
			'default':None},
			{'key':'list',
			'default':False},
			{'key':'listContents',
			'default':[]},
			{'key':'builtinList',
			'default':False},
			{'key':'searchList',
			'default':False},
			{'key':'searchKey',
			'default':None},
			{'key':'cfgFile',
			'default':None},
			{'key':'cfgStr',
			'default':''},
			{'key':'cfgList',
			'default':[]}
			]
	options = OptionsDatabase(values, rules)
	if not options.value:
		options.value = ''
	options.value, options.extraArgs = parseValue(options.value.split(' '))
	options.value, options.extraArgs = list2str(options.value, ' '), list2str(options.extraArgs, ' ')
	if options.local and type(options.local) == bool:
		options.local = getLocalRepo()
	if options.list and ((type(options.list) == bool) or ('search-' in options.list or 's-' in options.list)):
		options.list = 'bltin' if (type(options.list) == bool) else options.list
		options.builtinList = True
		options.searchList = True if ('search-' in options.list or 's-' in options.list) else False
		if options.searchList:
			options.searchKey = options.list.split('-')[1]
	if options.smart and type(options.smart) == bool:
		options.smart = 'PackagesList.txt'
	if options.export and type(options.export) == bool:
		options.export = 'PackagesList.txt'
	if options.list and type(options.list) == str:
		options.list = options.list.replace('local.', options.local+'/' if options.local else '')
	if options.smart and type(options.smart) == str:
		options.smart = options.smart.replace('local.', options.local+'/' if options.local else '')
	if options.export and type(options.export) == str:
		options.export = options.export.replace('local.', options.local+'/' if options.local else '')

	if options.smart:
		if os.path.exists(options.smart):
			f = open(options.smart)
			options.cfgList = f.read().splitlines()
			f.close()
		else:
			options.cfgFile = open(options.smart, 'w')
		if options.cfgFile is None:
			options.cfgFile = open(options.smart, 'w')
		options.cfgStr = ''
		for package in options.cfgList:
			options.cfgStr += package+'\n'
		if options.cfgStr.splitlines():
			options.cfgFile.write(options.cfgStr)
			options.cfgFile.flush()

	if options.list:
		if options.builtinList:
			options.listContents += _p
		if options.searchList:
			newListContents = []
			for c in options.listContents:
				if options.searchKey in c:
					newListContents.append(c)
			options.listContents = newListContents
		if not options.builtinList:
			if os.path.exists(options.list):
				options.listContents += open(options.list).read().splitlines()
			else:
				options.listContents.append(options.value)
	else:
		options.listContents.append(options.value)

	if not action:
		printErr('argument is invalid.')
		return
	if action in ['install', 'download', 'wheel']:
		VAL1 = ValueWidget(0)
		VAL2 = ValueWidget(0)
		form = '$1 ignored, $2 $MSG $BAR' if settings.ui in ['small', 'verysmall'] else '$TIME ($VAL/$MAX) $1 ignored, $2 $MSG $BAR $PERC% completed'
		progress = Progress(maxVal=len(options.listContents),
							msg=action+'ed', msgForm=form,
							replaces=[['$TIME', TimeWidget(hour=False)], ['$BAR', BarWidget(fillPerPercent=10 if settings.ui == 'verysmall' else 5)], ['$1', VAL1], ['$2', VAL2]],
							inline=True)
		for c in range(len(options.listContents)):
			value = options.listContents[c]
			if value is None:
				progress.newline()
				printErr('name not entered.')
				VAL1.value += 1
				progress.update(c+1)
				continue
			if options.value and not ' ' in options.value and not options.value.startswith('-'):
				if not options.value in value:
					VAL1.value += 1
					progress.update(c+1)
					continue
			elif options.value and ' ' in options.value:
				for v in options.value.split(' '):
					if not v.startswith('-'):
						if not options.value in value:
							VAL1.value += 1
							progress.update(c+1)
							continue
			if options.smart:
				if value in options.cfgList:
					VAL1.value += 1
					progress.update(c+1)
					continue
			progress.newline()
			try:
				if options.local:
					runAsMain(str('pip '+action+'$VAL'+'$EX'+' --no-index -f '+options.local).replace('$VAL', (' '+value if value else '')).replace('$EX', (' '+options.extraArgs) if options.extraArgs else ''))
				else:
					runAsMain(str('pip '+action+'$VAL'+'$EX').replace('$VAL', (' '+value if value else '')).replace('$EX', (' '+options.extraArgs) if options.extraArgs else ''))
			except:
				pass
			if options.smart:
				options.cfgList.append(value)
				options.cfgFile.write(value+'\n')
				options.cfgFile.flush()
			VAL2.value += 1
			progress.update(c+1)
		progress.newline()
		if options.smart:
			options.cfgFile.close()

	elif action == 'search':
		searchResult = []
		if options.value in options.listContents:
			options.listContents.remove(options.value)
		if options.listContents:
			for p in options.listContents:
				if options.value:
					if options.value in p:
						searchResult.append(p)
				else:
					searchResult.append(p)
		elif options.local:
			for f in os.listdir(options.local):
				if f.endswith('.tar.gz') or f.endswith('.whl') or f.endswith('.zip'):
					if options.value:
						if options.value in f:
							searchResult.append(f)
					else:
						searchResult.append(f)
		else:
			try: runAsMain('pip '+action+' '+options.value)
			except: pass
		if options.export:
			f = open(options.export, 'w')
			ss = ''
			for p in searchResult:
				ss += p+'\n'
			f.write(ss)
			f.flush()
			f.close()
			printMsg('search result exported to '+options.export)
		else:
			for p in searchResult:
				printMsg(p, colorize=False)
	elif action == 'version':
		printMsg(len(_p))
	else:
		printErr('argument is invalid.')
		return