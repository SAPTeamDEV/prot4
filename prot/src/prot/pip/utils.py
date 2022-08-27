from ..settings import settings

def parseValue(value):
	args = []
	vals = []
	for v in value:
		if v.startswith('-'):
			args.append(v)
		elif v.startswith('+'):
			args[len(args) - 1] += ' ' + v.replace('+', '')
		else:
			vals.append(v)
	return vals, args

def getLocalRepo():
	if settings.repo == 'default':
		return DEFAULT_REPOSITORY
	else:
		return settings.repo

def convertUpdatePackage(iFile=None, oFile=None, ofFile='txt'):
	printMsg('converting file to '+ofFile+' format...')
	ifFile = 'txt' if not ofFile == 'txt' else 'py'
	if type(iFile) == bool:
		iFile = 'PackagesList.'+ifFile
	if type(oFile) == bool:
		oFile = 'PackagesList.'+ofFile
	if not os.path.exists(iFile):
		printErr('import argument not entered.')
		return
	data = decode(iFile, ifFile)
	try:
		open(oFile, 'w').write(encode(data, ofFile))
	except PermissionError:
		printErr('permission denied.')
		return
	printMsg('converted '+iFile+' to '+oFile+'.')

def decode(file, type='txt'):
	if type == 'txt':
		return open(file).read().splitlines()
	else:
		return getVarFromFile(file, 'packagesList')

def encode(data, type='txt'):
	if type == 'txt':
		string = ''
		for d in data:
			string += d+'\n'
		return string
	else:
		return 'packagesList = '+str(data)

def updateBuiltinList(export=False, pList=False, fList='txt'):
	if export and pList:
		convertUpdatePackage(pList, export, fList)
		return
	if xmlrpclib is None and not pList:
		printErr('xmlrpc is required.')
		return
	global _p
	if not export:
		printMsg('current version is '+str(len(_p)))
	printMsg('checking for updates...' if not export else 'getting list...')
	try:
		if pList:
			if type(pList) == bool:
				pList = 'PackagesList.txt' if fList == 'txt' else 'packagesList.py'
			if fList == 'txt':
				pl = open(pList).read().splitlines()
			else:
				pl = getVarFromFile(pList, 'packagesList')
		else:
			client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')
			pl = client.list_packages()
	except:
		printErr('update failed.' if not export else 'error occured while getting list.')
		return
	if len(pl) <= len(_p) and not export:
		printMsg('built in list already updated.')
		return
	if settings.orderedBuiltinList:
		pl.sort()
	try:
		if export:
			if type(export) == bool:
					export = 'PackagesList.txt' if fList == 'txt' else 'packagesList.py'
			f = open(export, 'w')
			f.write(encode(pl, fList))
			f.flush()
			f.close()
		else:
			_p = pl
			f = open(os.path.join(os.path.split(__file__)[0], 'packagesList.py'), 'w')
			f.write('packagesList = '+str(_p))
			f.flush()
			f.close()
	except PermissionError:
		printErr('permission denied.')
		return
	printMsg('built in list updated to version '+str(len(_p))+'.' if not export else 'list exported to '+export+'.' if fList == 'txt' else 'list exported to '+export+' with python format.')
