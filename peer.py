import asyncio
from bitstring import BitArray

from core.response_handler import PeerResponseHandler as Handler
from core.response_parser import PeerResponseParser as Parser
from core.message_generator import MessageGenerator as Generator


class PeersManager:
	def __init__(self, peer_list):
		self.peer_list = peer_list
		self.black_list = list()


	def dispatch(self, piece_num):
		for peer in self.peer_list:
			ip, port = peer.address
			if not ip in self.black_list:
				if peer.pieces[piece_num]:
					peer.busy = True
					self.peer_list.remove(peer)
					return peer
		# Raise ValueError if no peers are available
		raise ValueError("No Peers Available")


	def retrieve(self, peer):
		peer.busy = False
		self.peer_list.append(peer)


	def blacklist(self, ip):
		self.black_list.append(ip)


class Peer:
	def __init__(self, address, torrent_info):
		self.address = address
		self.torrent_info = torrent_info

		self.active = False
		self.busy = False

		self.choking_me = True
		self.am_interested = False
		self.has_handshaked = False
		self.has_bitfield = False

		# create empty BitArray of length equal to total number of pieces in the torrent
		num_pieces = len(torrent_info['piece_hashmap'])
		self.pieces = BitArray(num_pieces)


	def __repr__(self):
		return f"Peer({self.address})"


	async def connect(self):
		ip, port = self.address
		try:
			# creating connection variable for readability
			connection = asyncio.open_connection(ip, port)
			self.reader, self.writer = await asyncio.wait_for(connection, timeout=3)
			self.active = True
			print(f"Opened Connection to {self}")

		# ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection
		# ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host
		# ConnectionAbortedError: [WinError 10053] An established connection was aborted by the software in your host machine
		except(ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError, OSError):
			await self.disconnect(f"Connection Refused/Reset/Aborted in CONNECT!")

		except asyncio.TimeoutError: await self.disconnect("Timed out while connecting!")


	async def disconnect(self, message=''):
		self.active = False
		if hasattr(self, 'writer'):
			await self.writer.drain()
			self.writer.close()
			await self.writer.wait_closed()
		print(f"{self} {message} Closed Connnection")


	async def handshake(self):
		# send handshake after opening a connection successfully
		if self.active:
			ih = self.torrent_info['info_hash']
			handshake_message = Generator.gen_handshake(ih)
			response = await self.send_message(handshake_message)
			artifacts = Parser(response).parse()
			await Handler(artifacts, Peer=self).handle()



	async def intrested(self):
		# send intrested message if handshake is done and client is choked
		if self.active and self.has_handshaked:# and not self.choking_me:
			interested_message = Generator.gen_interested()
			response = await self.send_message(interested_message)
			artifacts = Parser(response).parse()
			await Handler(artifacts, Peer=self).handle()


	async def send_message(self, message, timeout=3, _debug=False):
		# Raise error if send_message() is called but peer is inactive
		if not self.active:
			raise BrokenPipeError(f"Connection to {self} has been closed")
			
		EMPTY_RESPONSE_THRESHOLD = 5
		response_buffer = bytes()
		self.writer.write(message)
		try:
			while True:
				response = await asyncio.wait_for(self.reader.read(1024), timeout=timeout)
				response_buffer += response

				if _debug: print(f"{self}, {response=}")
				if len(response) <= 0: EMPTY_RESPONSE_THRESHOLD -= 1
				if EMPTY_RESPONSE_THRESHOLD < 0:
					await self.disconnect(f"Empty Response Threshold Exceeded!")

		# Timeout here is intentional and guaranteed. This is done to
		# receive full message because message gets sent in parts
		except asyncio.TimeoutError:
			...

		# ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection
		# ConnectionAbortedError: [WinError 10053] An established connection was aborted by the software in your host machine
		# ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host
		except(ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError):
			await self.disconnect(f"Connection Refused/Reset/Aborted in SEND!")

		finally:
			return response_buffer



if __name__ == "__main__":
	...
