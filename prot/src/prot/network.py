import socket

from .progress import Progress, ValueWidget

def getIP():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		sock.connect(('10.255.255.255', 1))
		ip = sock.getsockname()[0]
	except:
		ip = '127.0.0.1'
	finally:
		sock.close()
	return ip

def checkAvailable(address, timeout=0.5):
	sock = socket.socket()
	sock.settimeout(timeout)
	try:
		sock.connect(address)
		sock.close()
		return True
	except:
		return False

def netAvailable(timeout=0.5):
	return checkAvailable(('www.google.com'), timeout)

def getBaseAddress(address):
	return '.'.join(address.split('.')[:3])

def netScan(port=80, timeout=0.5):
	ports = port if type(port) == list else [port]
	baseAddr = getBaseAddress(getIP())
	hostsAvail = []
	for n in range(256):
		host = baseAddr + '.' + str(n)
		for p in ports:
			if checkAvailable((host, p), timeout):
				hostsAvail.append((host, p))
	return hostsAvail

def netAttack(addr, times):
	val1 = ValueWidget(' starting')
	prog = Progress(maxVal=times * 2, msgForm='$PERC% $MSG$1', replaces=[['$1', val1]], inline=True)
	for t in range(times):
		val1.value = ' connecting to ' + str(addr[0]) + ':' + str(addr[1])
		prog.next()
		sock = socket.socket()
		sock.connect(addr)
		val1.value = ' disconnecting from ' + str(addr[0]) + ':' + str(addr[1])
		prog.next()
		sock.close()
	val1.value = ''
	prog.show()
	prog.newline()
