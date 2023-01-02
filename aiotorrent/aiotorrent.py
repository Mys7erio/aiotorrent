import asyncio
import bencode
import hashlib
import platform

from aiotorrent.peer import Peer
from aiotorrent.core.util import chunk, PieceWriter
from aiotorrent.core.file_utils import FileTree
from aiotorrent.tracker_factory import TrackerFactory
from aiotorrent.downloader import FilesDownloadManager


# Asyncio throws runtime error if the platform is windows
# RuntimeError: Event loop is closed
# FOUND FIX: https://stackoverflow.com/a/66772242
if platform.system() == 'Windows':
	asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())



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
		self.files = None # This will be replaced with a file_tree object

		# Check if this torrent has multiple files
		self.has_multiple_files = True if 'files' in data['info'] else False

		size = int()
		peers = list()
		trackers = list()
		piece_hashmap = dict()
		announce = data['announce'] if 'announce' in data else None # announce is a string
		files = data['info']['files'] if self.has_multiple_files else self.name
		piece_len = data['info']['piece length']

		# If torrent has multiple files, set torrent
		# size to sum of length of all individual files
		if self.has_multiple_files:
			size = sum([file['length'] for file in files])
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
			piece_hashmap[index] = piece

		self.torrent_info = {
			'name': data['info']['name'],
			'size': size,
			'files': files,
			'piece_len': piece_len,
			'info_hash': info_hash,
			'piece_hashmap': piece_hashmap,
			'peers': peers,
			'trackers': trackers,
		}

		# Add announce url to trackers list if announce exists
		if announce: self.torrent_info['trackers'].append(announce)

		# Adding trackers to torrent info. Tracker is a list that contains a string
		if 'announce-list' in data:
			for tracker in data['announce-list']:
				tracker = tracker[0]
				if not tracker in self.torrent_info['trackers']:
					self.torrent_info['trackers'].append(tracker)

		self.files = FileTree(self.torrent_info)
		[print(file) for file in self.torrent_info['files']]
		print("*"*64)


	def _contact_trackers(self):
		# Create tracker objects using Tracker Factory Class
		for tracker in self.torrent_info['trackers']:
			self.trackers.append(
				TrackerFactory(tracker, self.torrent_info)
				)
		print(f"Got {len(self.torrent_info['trackers'])} trackers for this torrent")



	def _get_peers(self):
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


	def show_files(self):
		for file in self.files:
			print(f"File: {file}")


	async def init(self):
		# Contact Trackers and get peers
		self._contact_trackers()
		self._get_peers()

		# Use list comprehension to create and execute peer functions in parallel
		connections = [peer.connect() for peer in self.peers]
		await asyncio.gather(*connections)

		handshakes = [peer.handshake() for peer in self.peers]
		await asyncio.gather(*handshakes)

		interested_msgs = [peer.intrested() for peer in self.peers]
		await asyncio.gather(*interested_msgs)

		# Info
		active_peers = [peer for peer in self.peers if peer.has_handshaked]
		active_trackers = [tracker for tracker in self.trackers if tracker.active]
		print(f"{len(active_peers)} peers active")
		print(f"{len(active_trackers)} trackers active")


	async def download(self, file):
		active_peers = [peer for peer in self.peers if peer.has_handshaked]
		fd_man = FilesDownloadManager(self.torrent_info, active_peers)
		directory = self.torrent_info['name']

		with PieceWriter(directory, file) as piece_writer:
			async for piece in fd_man.get_file(file):
				piece_writer.write(piece)


	async def __generate_torrent_stream(self, file):
		active_peers = [peer for peer in self.peers if peer.has_handshaked]
		fd_man = FilesDownloadManager(self.torrent_info, active_peers)
		async for piece in fd_man.get_file(file):
			yield piece.data


	async def stream(self, file, host="127.0.0.1", port=8080):
		from starlette.applications import Starlette
		from starlette.responses import StreamingResponse
		from starlette.routing import Route

		async def homepage(request):
			return StreamingResponse(
				self.__generate_torrent_stream(file),
				media_type='video/mp4'
			)

		app = Starlette(debug=True, routes=[
				Route('/', homepage),
		])

		import uvicorn
		config = uvicorn.Config(app, host=host, port=port)
		server = uvicorn.Server(config)
		await server.serve()



if __name__ == '__main__':
	torrent = Torrent('pytorrent/bbb.torrent')
	print(torrent.announce)
	print(torrent.trackers)
	print(torrent.udp_trackers)