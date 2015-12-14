import miniupnpc

class UpnpPortMap:
	'''A class for controling a UPnP Internet Gateway Device
	
	Objects of this class should be used with a with statement in order to
	ensure the port mapping is destroyed correctly, for example:
	with UpnpPortMap(12345, "TCP") as port:
		pass'''
	def __init__(self, local_port, proto):
		'''Forward a port using UPnP
		
		Arguments:
		local_port -- The port of the server to forward to on the local machine
		proto      -- The protocol to forward. Either 'TCP' or 'UDP'
		'''
		
		# Make sure the arguments are sane
		assert(proto == 'TCP' or proto == 'UDP')
		assert(isinstance(local_port, int))
		assert(local_port > 0 and local_port < 65536)
		
		# Discover the UPnP devices
		self._upnp = miniupnpc.UPnP()
		self._upnp.discoverdelay = 250
		self._upnp.discover()
		
		# Select the Internet Gateway Device
		self._upnp.selectigd()
		self._local_ip = self._upnp.lanaddr
		self._public_ip = self._upnp.externalipaddress()
		
		# Find an available port
		self._protocol = proto
		self._local_port = local_port
		self._public_port = None
		for public_port in range(49152, 65536):
			if self._upnp.getspecificportmapping(public_port, 'TCP') is None:
				self._public_port = public_port
				break
		if self._public_port is None:
			raise Exception('Could not find an unused UPnP port')
		
		# Forward the port
		if not self._upnp.addportmapping (
			self._public_port, 'TCP', self._local_ip, self._local_port,
			'TriplePong Server', ''
		): raise Exception('Could not forward UPnP port')
	
	def GetExternalIp(self):
		'''Return the external IP address of the mapping'''
		return self._public_ip
	
	def GetExternalPort(self):
		'''Return the external port of the mapping'''
		return self._public_port
	
	def __enter__(self):
		return self
	
	def __exit__(self, exc_type, exc_value, traceback):
		for _ in range(4): # Try four times. If it still fails, give up.
			if self._upnp.deleteportmapping(self._public_port, 'TCP'):
				break

# This serves as a simple test of the port forwarding facilities. It's hard to
# write a complete unit test, as it would fail on a machine not benind a UPnP
# compatible NAT (which I consider to be a bad failure condition).
if __name__ == '__main__':
	with UpnpPortMap(12345, "TCP") as port:
		print ('%s:%u' % (port.GetExternalIp(), port.GetExternalPort()))