import asyncio
import logging
from bitstring import BitArray

from aiotorrent.core.response_handler import PeerResponseHandler as Handler
from aiotorrent.core.response_parser import PeerResponseParser as Parser
from aiotorrent.core.message_generator import MessageGenerator as Generator


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Peer:
	def __init__(self, address, torrent_info, priority = 10):
		self.address = address
		self.torrent_info = torrent_info

		self.active = False
		self.priority = priority
		# self.busy = False
		self.total_disconnects = 0

		self.choking_me = True
		self.am_interested = False
		self.has_handshaked = False
		self.has_bitfield = False

		# create empty BitArray of length equal to total number of pieces in the torrent
		num_pieces = len(torrent_info['piece_hashmap'])
		self.pieces = BitArray(num_pieces)


	def __repr__(self):
		return f"Peer({self.address})"
	

	def __lt__(self, other):
		return self.priority < other.priority


	async def connect(self):
		ip, port = self.address
		try:
			# creating connection variable for readability
			connection = asyncio.open_connection(ip, port)
			self.reader, self.writer = await asyncio.wait_for(connection, timeout=3)
			self.active = True
			logger.debug(f"Opened Connection to {self}")

		# ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection
		# ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the remote host
		# ConnectionAbortedError: [WinError 10053] An established connection was aborted by the software in your host machine
		except(ConnectionRefusedError, ConnectionResetError, ConnectionAbortedError, OSError):
			await self.disconnect(f"Connection Refused/Reset/Aborted in CONNECT!")

		except asyncio.TimeoutError: await self.disconnect("Timed out while connecting!")


	async def disconnect(self, message=''):
		self.active = False
		self.total_disconnects += 1
		if hasattr(self, 'writer'):
			await self.writer.drain()
			self.writer.close()
			await self.writer.wait_closed()
		logger.debug(f"{self} {message} Closed Connnection")


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


	async def send_message(self, message, timeout=3):
		# Raise error if send_message() is called but peer is inactive
		# If send_message was called and the current status of the peer is not active
		# This means that this peer dropped the connection mid execution
		# So, we will re-establish a connection and re-raise the exception
		if not self.active:
			if self.total_disconnects > 10:
				return
			await self.connect()
			await self.handshake()
			await self.intrested()

			if self.active:
				logger.warning(f"Tried sending message to inactive {self}. Successfully re-established connection!")
			else:
				logger.warning(f"Tried sending message to inactive {self}. Failed to re-establish connection!")

			# Now raise BrokenPipeError so that the caller of send_message() can handle it
			raise BrokenPipeError(f"Tried sending message to inactive peer")

		if not self.active:
			raise BrokenPipeError(f"Connection to {self} has been closed")
			
		EMPTY_RESPONSE_THRESHOLD = 5
		response_buffer = bytes()
		self.writer.write(message)
		try:
			while True:
				response = await asyncio.wait_for(self.reader.read(1024), timeout=timeout)
				response_buffer += response

				logger.debug(f"{self}, {response=}")
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


	def update_piece_info(self, piece_num: int, has_piece: bool):
		# Utility function to update piece information of peer
		self.pieces[piece_num] = has_piece



