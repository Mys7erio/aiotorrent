import asyncio
import logging
from random import randint
from struct import pack, unpack
from ipaddress import IPv4Address
from urllib.parse import urlparse, ParseResult

from aiotorrent.core.util import chunk


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class TrackerBaseClass:
	def __init__(self, tracker_addr: ParseResult, torrent_info: dict) -> None:
		# get first element from the array
		# tracker url is in string format
		tracker_addr = urlparse(tracker_addr)

		self.scheme: str = tracker_addr.scheme
		self.hostname: str = tracker_addr.hostname
		self.port: int = tracker_addr.port
		self.key: int = randint(10000, 99999)

		self.active: bool = False
		# Missing typehint
		self.torrent_info = torrent_info

		self.peers = []
		self.connect_response: dict = {}
		self.announce_response: dict = {}


	def gen_connect(self) -> bytes:
		connection_id = 0x41727101980
		action = 0
		transaction_id = randint(1, 65536)

		message = pack(
			'>QII',
			connection_id,
			action,
			transaction_id,
		)

		return message


	def gen_announce(self, connection_id: int, transaction_id: int) -> bytes:
		# Create a dictionary with all the properties of
		# the UDP connect message

		# Ignore redundant connection and transaction vairables being redclared
		connection_id = connection_id				# connection_id, # 64 bit integer
		action = 1									# 32 bit integer; announce
		transaction_id = transaction_id				# 32 bit integer
		info_hash = self.torrent_info['info_hash']	# 20 byte string
		peer_id = b"ABCD" + b"X"*16					# 20 byte string; Should be the same and only change if the client restarts
		downloaded = 0								# 64 bit integer
		left = self.torrent_info['size']			# 64 bit integer
		uploaded = 0								# 64 bit integer
		event = 2									# 32 bit integer; started
		ip_address = 0								# 32 bit integer; 0 is default
		key = self.key								# 32 bit integer
		num_want = -1								# 32 bit integer; -1 is default
		port = 6887									# 16 bit integer; should be between 6881 & 6889

		# Pack the message before sending. Packing breakdown
		# Q -> 64 bit integer
		# I -> 32 bit integer
		# s	-> 1 byte string[]
		# 20s -> 20 byte string[]
		# i -> 32 bit unsigned integer
		# H -> 16 bit integer

		message = pack(
			'>QII20s20sQQQIIIiH',
			connection_id,
			action,
			transaction_id,
			info_hash,
			peer_id,
			downloaded,
			left,
			uploaded,
			event,
			ip_address,
			key,
			num_want,
			port
		)

		return message
	

	def parse_connect(self, response: bytes) -> dict[str, int]:
		action, transaction_id, connection_id = unpack('>IIQ', response)

		connect_response = {
			'action': action,
			'transaction_id': transaction_id,
			'connection_id': connection_id
		}

		return connect_response
	

	def parse_announce(self, response: bytes) -> dict[str, int | list[tuple[str, int]]]:
		# seperate the properties (20 bytes / 5 properties) and IP list
		response, raw_IPs = response[:20], response[20:]

		# extract the variables with known length
		action, transaction_id, interval, leechers, seeders = unpack('>IIIII', response)

		ip_addresses = list()

		# iterate over the raw_IPs variable going over 6 bytes in each iteration
		# first 4 bytes is IP in decimal format and last 2 bytes is Port in integer format
		for ip_addr in chunk(raw_IPs, 6):
			ip, port = unpack('>IH', ip_addr)
			# convert ip from decimal to dotted format
			ip = IPv4Address(ip).compressed
			ip_addresses.append((ip, port))

		# Add peers received from the tracker to self
		self.peers = ip_addresses

		announce_response = {
			'action': action,
			'transaction_id': transaction_id,
			'interval': interval,
			'leechers': leechers,
			'seeders': seeders,
			'ip_addresses': ip_addresses
		}

		return announce_response





class UDPTracker(TrackerBaseClass):
	# Missing Typehint
	def __init__(self, tracker_addr: str, torrent_info) -> None:
		super().__init__(tracker_addr, torrent_info)


	def __repr__(self) -> str:
		return f"UDPTracker({self.hostname})"


	class UDPProtocolFactory(asyncio.DatagramProtocol):
		# Missing typehint
		def __init__(self, parent_obj):
			self.transport: None | asyncio.DatagramProtocol = None
			self.address = (parent_obj.hostname, parent_obj.port)
			self.parent_obj = parent_obj


		def connection_made(self, transport: asyncio.DatagramTransport) -> None:
			self.transport = transport
			# Send connection request when connected
			connect_req = self.parent_obj.gen_connect()
			logger.info(f"{self.parent_obj} Sending connect request to {self.address}")
			self.transport.sendto(connect_req)


		def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
			# Check if it's a connect response or an announce response and parse accordingly
			action = unpack('>I', data[:4])
			action = action[0]	# Unpack returns a tuple

			if action == 0:
				# if action is 0, then it's a connect response
				logger.info(f"{self.parent_obj} Received connect response from {addr}")
				logger.debug(f"{self.parent_obj} Connect response: {data[:16]}")
				self.parent_obj.connect_response = self.parent_obj.parse_connect(data)

				# prepare announce request and send it
				connection_id = self.parent_obj.connect_response['connection_id']
				transaction_id = self.parent_obj.connect_response['transaction_id']
				announce_message = self.parent_obj.gen_announce(connection_id, transaction_id)

				# Send announce request
				logger.info(f"{self.parent_obj} Sending announce request to {self.address}")
				self.transport.sendto(announce_message)


			if action == 1:
				# If action is 1, then it's an announce response
				logger.info(f"{self.parent_obj} Received announce response from {addr}")
				logger.debug(f"{self.parent_obj} Announce response: {data[:32]}")
				self.parent_obj.announce_response = self.parent_obj.parse_announce(data)


	async def get_peers(self, timeout: int = 3) -> list[tuple[str, int]]:

		loop = asyncio.get_running_loop()
		await loop.create_datagram_endpoint(
			lambda: self.UDPProtocolFactory(self),
			remote_addr = (self.hostname, self.port)
		)
		# This is necessary to wait for the response.
		# We can use asyncio.Event() for this as well
		await asyncio.sleep(timeout)

		return self.peers



class HTTPTracker(TrackerBaseClass):
	def __init__(self, *args):
		self.active = False
		logger.debug(f"	http object skipped...")


	async def get_peers(self):
		self.peers = []
		await asyncio.sleep(1)
		return []



class WSSTracker(TrackerBaseClass):
	def __init__(self, *args):
		self.active = False
		self.peers = []
		logger.debug(f"	wss object skipped")


	async def get_peers(self):
		await asyncio.sleep(1)
		return []

