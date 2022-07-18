from random import randint
from struct import pack
from urllib.parse import urlparse



class TrackerBaseClass:
	def __init__(self, tracker_addr, torrent_info):
		# get first element from the array
		# tracker url is in string format
		tracker_addr = urlparse(tracker_addr)

		self.scheme = tracker_addr.scheme
		self.hostname = tracker_addr.hostname
		self.port = tracker_addr.port
		self.key = randint(10000, 99999)

		self.torrent_info = torrent_info

		self.active = False


	def __repr__(self):
		return self.hostname


	def gen_connect(self):
		connect_message = {
			"connection_id":  0x41727101980,
			"action": 0,
			"transaction_id": randint(1, 65536)
		}

		message = pack(
			'>QII',
			connect_message['connection_id'],
			connect_message['action'],
			connect_message['transaction_id']
		)

		return message


	def gen_announce(self, connection_id, transaction_id):
		# Create a dictionary with all the properties of
		# the UDP connect message
		announce_message = {
			'connection_id': connection_id, # 64 bit integer
			'action': 1, # 32 bit integer; announce
			'transaction_id': transaction_id, # 32 bit integer
			'info_hash': self.torrent_info['info_hash'], # 20 byte string
			'peer_id': b"ABCD" + b"X"*16, # 20 byte string; Should be the same and only change if the client restarts
			'downloaded': 0, # 64 bit integer
			'left': self.torrent_info['size'], # 64 bit integer
			'uploaded': 0, # 64 bit integer
			'event': 2, # 32 bit integer; started
			'IP address': 0, # 32 bit integer; 0 is default
			'key': self.key, # 32 bit integer
			'num_want': -1, # 32 bit integer; -1 is default
			'port': 6887 # 16 bit integer; should be between 6881 & 6889
		}
		# Pack the message before sending
		# packing breakdown
		# ***
			# Q -> 64 bit integer
			# I -> 32 bit integer
			# s	-> 1 byte string[]
			# 20s -> 20 byte string[]
			# i -> 32 bit unsigned integer
			# H -> 16 bit integer
		# ***
		message = pack(
			'>QII20s20sQQQIIIiH',
			announce_message['connection_id'],
			announce_message['action'],
			announce_message['transaction_id'],
			announce_message['info_hash'],
			announce_message['peer_id'],
			announce_message['downloaded'],
			announce_message['left'],
			announce_message['uploaded'],
			announce_message['event'],
			announce_message['IP address'],
			announce_message['key'],
			announce_message['num_want'],
			announce_message['port']
		)

		return message

	# breakpoint()