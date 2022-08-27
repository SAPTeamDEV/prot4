try:
	from .packages_data import packagesList as _p
except:
	_p = []

__version__ = str(len(_p))
DEFAULT_REPOSITORY = 'Pypi'

