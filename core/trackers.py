import socket
from struct import unpack
from ipaddress import IPv4Address

from core.trackerbase import TrackerBaseClass
from core.util import chunk



class UDPTracker(TrackerBaseClass):
	def __init__(self, tracker_addr, torrent_info):
		super().__init__(tracker_addr, torrent_info)
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.settimeout(3)

		try:
			self.connect_response = self.send_connect(sock)
			self.announce_response = self.send_announce(
				self.connect_response['connection_id'],
				self.connect_response['transaction_id'],
				sock
			)
			self.active = True

		except socket.gaierror:
			print(f"GAIError {self}")
		except socket.timeout:
			print(f"Timeout {self}")


	def get_peers(self):
		# return peer list if self has announce response attribute else return empty list
		if hasattr(self, 'announce_response'):
			peers = self.announce_response['ip_addresses']
		else:
			peers = list()
		return peers


	def send_connect(self, sock):
		address = (self.hostname, self.port)
		connect_message = self.gen_connect()

		msize = sock.sendto(connect_message, address)
		response = sock.recv(1024)

		action, transaction_id, connection_id = unpack('>IIQ', response)
		connect_response = {
			'action': action,
			'transaction_id': transaction_id,
			'connection_id': connection_id
		}

		return connect_response


	def send_announce(self, connection_id, transaction_id, sock):
		address = (self.hostname, self.port)
		announce_message = self.gen_announce(connection_id, transaction_id)

		msize = sock.sendto(announce_message, address)
		response = sock.recv(4096)

		# seperate the properties (20 bytes / 5 properties) and IP list
		response, raw_IPs = response[:20], response[20:]

		# extract the variables with known length
		action, transaction_id, interval, leechers, seeders = unpack('>IIIII', response)

		ip_addresses = list()
		# iterate over the raw_IPs variable going over 6 bytes
		# each iteration grabs the first 6 bytes
		# first 4 bytes is IP in decimal format and last 2 bytes is Port in integer format
		# pass ip through IPv4Address() to => string format

		for ip_addr in chunk(raw_IPs, 6):
			ip, port = unpack('>IH', ip_addr)
			# convert ip from decimal to dotted format
			ip = IPv4Address(ip).compressed
			ip_addresses.append((ip, port))
			# print('fucceff', (ip, port))

		announce_response = {
			'action': action,
			'transaction_id': transaction_id,
			'interval': interval,
			'leechers': leechers,
			'seeders': seeders,
			'ip_addresses': ip_addresses
		}

		print(f"Active {self}")
		return announce_response



class HTTPTracker(TrackerBaseClass):
	def __init__(self, *args):
		self.active = False
		print(f"	http object skipped...")



	def get_peers(self):
		return []



class WSSTracker(TrackerBaseClass):
	def __init__(self, *args):
		self.active = False
		print(f"	wss object skipped")


	def get_peers(self):
		return []




if __name__ == "__main__":
	breakpoint()