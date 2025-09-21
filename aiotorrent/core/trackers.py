import asyncio
import logging
from random import randint
from typing import Literal
from socket import gaierror
from struct import pack, unpack
from ipaddress import IPv4Address
from http.client import HTTPConnection, HTTPSConnection
from urllib.parse import urlparse, urlencode, ParseResult

from aiotorrent.core.util import chunk
from aiotorrent.core.bencode_utils import bencode_util


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


PEER_ID = b"aiotorrent-XXXXXXXXX"

#TODO: Aggregate global variables in a seperate config file / dictionary

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


	def gen_connect_udp(self) -> dict:
		connection_id = 0x41727101980
		action = 0
		transaction_id = randint(1, 65536)

		connect_params = {
			'connection_id': connection_id,
			'action': action,
			'transaction_id': transaction_id
		}

		return connect_params

	@staticmethod
	def serialize_connect(format: Literal["bytes"] | Literal["url"], connect_params: dict) -> bytes | dict:
		if	format == "bytes":
			return pack(
				'>QII',
				connect_params['connection_id'],
				connect_params['action'],
				connect_params['transaction_id'],
			)

		else: return urlencode(connect_params)



	def gen_announce_udp(self, connection_id: int = 0, transaction_id: int = 0) -> dict:
		# Create a dictionary with all the properties of
		# the UDP connect message

		announce_params = {
			'connection_id': connection_id,					# 64 bit integer
			'action': 1,									# 32 bit integer; announce
			'transaction_id': transaction_id,				# 32 bit integer
			'info_hash': self.torrent_info['info_hash'],	# 20 byte string
			'peer_id': PEER_ID,								# 20 byte string; Should be the same and only change if the client restarts
			'downloaded': 0,								# 64 bit integer
			'left': self.torrent_info['size'],				# 64 bit integer
			'uploaded': 0,									# 64 bit integer
			'event': 2,										# 32 bit integer; started
			'ip_address': 0,								# 32 bit integer; 0 is default
			'key': self.key,								# 32 bit integer
			'num_want': 200,								# 32 bit integer; -1 is default
			'port': 6887									# 16 bit integer; should be between 6881 & 6889
		}

		return announce_params

	def gen_announce_http(self):
		# no_peer_id: Not included because this option is ignored if compact is enabled

		# ip: Not included because this option is only needed in the case where the IP address
		# that the request came in on is not the IP address of the client.

		# key, trackerid: Optional, so not included

		announce_params = {
			'info_hash': self.torrent_info['info_hash'],
			'peer_id': PEER_ID,
			'port': 6887,
			'uploaded': 0,
			'downloaded': 0,
			'left': self.torrent_info['size'],
			'compact': 1,
			'event': 'started',
			'num_want': 200
		}

		return announce_params

	def serialize_announce(format: Literal["bytes"] | Literal["url"], announce_params: dict) -> bytes | dict:
		# Pack the message before sending. Packing breakdown
		# Q -> 64 bit integer
		# I -> 32 bit integer
		# s	-> 1 byte string[]
		# 20s -> 20 byte string[]
		# i -> 32 bit unsigned integer
		# H -> 16 bit integer

		if format == "bytes":
			return pack(
			'>QII20s20sQQQIIIiH',
			announce_params['connection_id'],
			announce_params['action'],
			announce_params['transaction_id'],
			announce_params['info_hash'],
			announce_params['peer_id'],
			announce_params['downloaded'],
			announce_params['left'],
			announce_params['uploaded'],
			announce_params['event'],
			announce_params['ip_address'],
			announce_params['key'],
			announce_params['num_want'],
			announce_params['port']
		)
	
		else: return urlencode(announce_params)


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
		return f"UDPTracker({self.hostname}:{self.port})"


	class UDPProtocolFactory(asyncio.DatagramProtocol):
		# Missing typehint
		def __init__(self, parent_obj):
			self.transport: None | asyncio.DatagramTransport = None
			self.address = (parent_obj.hostname, parent_obj.port)
			self.parent_obj = parent_obj


		def connection_made(self, transport: asyncio.DatagramTransport) -> None:
			self.transport = transport
			# Send connection request when connected
			connect_req_params = self.parent_obj.gen_connect_udp()
			connect_req = UDPTracker.serialize_connect("bytes", connect_req_params)
			logger.debug(f"{self.parent_obj} Sending connect request to {self.address}")
			self.transport.sendto(connect_req)


		def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
			# Check if it's a connect response or an announce response and parse accordingly
			action = unpack('>I', data[:4])
			action = action[0]	# Unpack returns a tuple

			if action == 0:
				# if action is 0, then it's a connect response
				logger.debug(f"{self.parent_obj} Received connect response from {addr}")
				logger.debug(f"{self.parent_obj} Connect response: {data[:16]}")
				self.parent_obj.connect_response = self.parent_obj.parse_connect(data)
				self.parent_obj.active = True

				# prepare announce request and send it
				connection_id = self.parent_obj.connect_response['connection_id']
				transaction_id = self.parent_obj.connect_response['transaction_id']
				announce_req_params = self.parent_obj.gen_announce_udp(connection_id, transaction_id)
				announce_req = UDPTracker.serialize_announce("bytes", announce_req_params)

				# Send announce request
				logger.debug(f"{self.parent_obj} Sending announce request to {self.address}")
				self.transport.sendto(announce_req)


			if action == 1:
				# If action is 1, then it's an announce response
				logger.info(f"{self.parent_obj} Received announce response from {addr}")
				logger.debug(f"{self.parent_obj} Announce response: {data[:32]}")
				self.parent_obj.announce_response = self.parent_obj.parse_announce(data)


	async def get_peers(self, timeout: int = 3) -> list[tuple[str, int]]:

		try:
			loop = asyncio.get_running_loop()
			await loop.create_datagram_endpoint(
				lambda: self.UDPProtocolFactory(self),
				remote_addr = (self.hostname, self.port)
			)
			# This is necessary to wait for the response.
			# We can use asyncio.Event() for this as well
			await asyncio.sleep(timeout)

		except gaierror as e:
			logger.warning(f"Failed to get address info for {self}")
		except Exception as e:
			self.peers = []
			logger.error(e)

		return self.peers



class HTTPTracker(TrackerBaseClass):
	def __init__(self, tracker_addr: str, torrent_info):
		# self.active = False
		super().__init__(tracker_addr, torrent_info)

		# Set http path parameter manually because the BaseTracker doesn't
		self.path = urlparse(tracker_addr).path


	def __repr__(self):
		return f"HTTPTracker({self.hostname}:{self.port})"


	async def get_peers(self):
		self.peers = []
		# It is acceptable with HTTP trackers to directly send the announce request,
		# without sending a connect request first (to reduce network overhead or some other reason)
		announce_req_raw = self.gen_announce_http()
		announce_req = HTTPTracker.serialize_announce("url", announce_req_raw)

		def connect_to_tracker(payload: str) -> dict:
			http_conn_factory = HTTPSConnection if self.scheme == "https" else HTTPConnection
			connection = http_conn_factory(host=self.hostname, port=self.port)
			final_query = f"{self.path}?{payload}"

			#TODO: Add useragent to the http request 
			connection.request("GET", final_query)
			response = connection.getresponse()

			if response.status == 200:
				self.active = True
				self.announce_response = bencode_util.bdecode(response.read())
				peer_list = self.announce_response['peers']
				for ip_addr in chunk(peer_list, 6):
					ip, port = unpack('>IH', ip_addr)
					ip = IPv4Address(ip).compressed
					self.peers.append((ip, port))

			else:
				logger.warning(f"Error fetching peers from {self}: Error Code: {response.status} - {response.reason}: {response.read()}")
				return []

		try:
			loop = asyncio.get_running_loop()
			result = await loop.run_in_executor(None, connect_to_tracker, announce_req)
			return result

		except Exception as e:
			logger.error(f"Error occured while connecting to {self}: {e}")
			return []



class WSSTracker(TrackerBaseClass):
	def __init__(self, *args):
		self.active = False
		self.peers = []
		logger.debug(f"	wss object skipped")


	async def get_peers(self):
		# await asyncio.sleep(1)

		return []

