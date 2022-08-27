import py_compile
import os

try:
	from docutils.core import publish_file
except:
	publish_file = None

from . import classes
from . import utils

from .exceptions import PackageNotFoundError

def pyCompile(source, usePEP=True, subfolders=False, deleteSource=False):
	if type(source) == list:
		fileList = source
	else:
		fileList = utils.makeTree(source=source, type='list', subfolders=subfolders)
	for file in fileList:
		if file.lower().endswith('.py'):
			py_compile.compile(file, cfile=None if usePEP else file+'c', optimize=2)
			if deleteSource:
				os.remove(file)

def rst2html(source, subfolders=False):
	if not publish_file:
		raise PackageNotFoundError('docutils')
	if type(source) == list:
		fileList = source
	else:
		fileList = utils.makeTree(source=source, type='list', subfolders=subfolders)
	for file in fileList:
		if file.lower().endswith('.rst'):
			publish_file(source_path=file, destination_path=file.split('.rst')[0]+'.html', writer_name='html')

def dict2matrix(obj):
	if not type(obj) == dict:
		raise TypeError('dict object is required.')
	matrix = []
	for m in obj:
		if type(obj[m]) == dict:
			matrix.append([m, dict2matrix(obj[m])])
		else:
			matrix.append(classes.Matrix([m, obj[m]]))
	return classes.Matrix(matrix)

def str2list(string):
	if not type(string) == str:
		raise TypeError('str object is required.')
	strList = []
	for s in string:
		strList.append(s)
	return strList

def list2str(listObj, space=''):
	if not type(listObj) == list:
		raise TypeError('list object is required.')
	string = ''
	for s in listObj:
		if string:
			string += space
		string += str(s)
	return string

def matrix2str(mat, space=''):
	if not type(mat) in [list, classes.Matrix]:
		raise TypeError('list or Matrix object is required.')
	string = ''
	for m in mat:
		if string:
			string += space
		if type(m) in [list, classes.Matrix]:
			string += str(matrix2str(m))
		elif type(m) == dict:
			string += str(matrix2str(dict2matrix(m)))
		else:
			string += str(m)
	return string
