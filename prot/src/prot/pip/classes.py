try:
	import xmlrpc.client as xmlrpclib
except:
	xmlrpclib = None

class PypiClient(object):
	def __init__(self):
		self.server = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')

	def allPackages(self):
		"""return a list of all server packages"""
		return self.server.list_packages()

	def userPackages(self, user):
		"""return a list of user packages"""
		return self.server.user_packages(user)

	def releaseUrls(self, name, version):
		"""return a list of release urls"""
		return self.server.release_urls(name, version)

	def packageRoles(self, name):
		"""return a list of package roles"""
		return self.server.package_roles(name)

	def packageReleases(self, name, show_hidden=True):
		"""return a list of package releases"""
		return self.server.package_releases(name, show_hidden)

	def releaseData(self, name, version):
		"""return dictionary with release data"""
		return self.server.release_data(name, version)
