import asyncio
import bencode
import hashlib
import platform
from asyncio.exceptions import TimeoutError, CancelledError

from core.util import chunk
from tracker_factory import TrackerFactory
from peer import Peer
from piece_manager import PieceManager


# Asyncio throws runtime error if the platform is windows
# RuntimeError: Event loop is closed
# FOUND FIX: https://stackoverflow.com/a/66772242
if platform.system() == 'Windows': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())



class Torrent:
	def __init__(self, torrent_file):
		torrent = open(torrent_file, 'rb')
		bencoded_data = torrent.read()
		torrent.close()

		# dict_keys(['files', 'name', 'piece length', 'pieces'])
		data = bencode.decode_torrent(bencoded_data)

		self.trackers = list()
		self.peers = list()
		self.name = data['info']['name']
		# Check if this torrent has multiple files
		self.has_multiple_files = True if 'files' in data['info'] else False

		size = int()
		peers = list()
		trackers = list()
		pieces = dict()
		announce = data['announce'] if 'announce' in data else None # announce is a string
		files = data['info']['files'] if self.has_multiple_files else self.name
		piece_len = data['info']['piece length']

		# Increase size for every file in this torrent
		# else set size to size of the single file
		if self.has_multiple_files:
			for file in files: size += file['length']
		else:
			size = data['info']['length']

		# re-encode info to -> bencode and then apply sha-1 to it
		raw_info_hash = bencode.encode_torrent(data['info'])
		info_hash = hashlib.sha1(raw_info_hash).digest()

		# get pieces and convert it from hexadecimal (string) to bytes object
		raw_pieces = data['info']['pieces']
		raw_pieces = bytes.fromhex(raw_pieces)

		# for every 20 byte in raw_pieces -> str, map index:piece (int:str) to pieces
		for index, piece in enumerate(chunk(raw_pieces, 20)):
			pieces[index] = piece

		self.torrent_info = {
			'size': size,
			'info_hash': info_hash,
			'files': files,
			'pieces': pieces,
			'piece_len': piece_len,
			'peers': peers,
			'trackers': trackers,
		}

		# Add announce url to trackers list if it exists
		if announce: self.torrent_info['trackers'].append(announce)
		
		# Adding trackers to torrent info. Tracker is a list that contains a string
		for tracker in data['announce-list']:
			tracker = tracker[0]
			if not tracker in self.torrent_info['trackers']:
				self.torrent_info['trackers'].append(tracker)

		print("*"*64)



	def contact_trackers(self):
		# Create tracker objects using Tracker Factory Class
		for tracker in self.torrent_info['trackers']:
			self.trackers.append(
				TrackerFactory(tracker, self.torrent_info)
				)
		print(f"Got {len(self.torrent_info['trackers'])} trackers for this torrent")



	def contact_peers(self):
		# Get peers address from each tracker and add them to
		# peer list if not already there
		for tracker in self.trackers:
			for peer in tracker.get_peers():
				if not peer in self.torrent_info['peers']:
					# Add peer address to torrent info
					self.torrent_info['peers'].append(peer)
					# create and add peers object to self
					self.peers.append(Peer(peer, self.torrent_info))

		print(f"Got {len(self.torrent_info['peers'])} Peers for this torrent")



	async def init(self):
		# Use list comprehension to create and execute peer functions in parallel
		connections = [peer.connect() for peer in self.peers]
		await asyncio.gather(*connections)

		handshakes = [peer.handshake() for peer in self.peers]
		await asyncio.gather(*handshakes)

		interested_msgs = [peer.intrested() for peer in self.peers]
		await asyncio.gather(*interested_msgs)

		# Info
		active_peers = [peer for peer in self.peers if peer.active]
		active_trackers = [tracker for tracker in self.trackers if tracker.active]
		print(f"{len(active_peers)} peers active")
		print(f"{len(active_trackers)} trackers active")


	async def download(self, piece=1):
		# sleep for 3 sec to recieve pending messages
		await asyncio.sleep(3)
		torrent_size = self.torrent_info['size']
		piece_size = self.torrent_info['piece_len']
		piece_hashmap = self.torrent_info['pieces']
		active_peers = [peer for peer in self.peers if peer.active]
		pm = PieceManager(torrent_size, piece_size, piece_hashmap, active_peers)
		await pm.get_all_pieces()



if __name__ == '__main__':
	torrent = Torrent('pytorrent/bbb.torrent')
	print(torrent.announce)
	print(torrent.trackers)
	print(torrent.udp_trackers)