from struct import unpack
from struct import error as UnpackError


class PeerResponseParser:
	def __init__(self, response, ParentClass=None):
		self.response = response
		self.ParentClass = ParentClass
		
		self.messages = {
		# self created index. Does not necessarily follow bittorrent protocol specification
			0: self.parse_choke,
			1: self.parse_unchoke,
			4: self.parse_have,
			5: self.parse_bitfield,
			7: self.parse_piece,
			19: self.parse_handshake,
		}


	async def parse(self, debug=False):
		self.debug = debug

		while self.response:
			try:
				# if first byte of response is 19 bytes, it's a handshake
				if self.response[0] == 19:
					await self.parse_handshake()
					continue #	issue #1

				# message len and id need to be class wide accessible because message len
				# needs to be updated in case of a bitfield and piece requests
				self.message_len = unpack('>I', self.response[:4])[0]
				self.message_id = unpack('>B', self.response[4:5])[0] if self.message_len != 0 else None
					
				# keep-alive messages have length 0 and no message_id
				if self.message_len == 0 and not self.message_id: await self.parse_keep_alive()

				# if msg id not in message index, clear response and close connection
				if self.message_id not in self.messages:
					ic("Weird:", self.message_id, self.message_len, self.response)
					self.response = bytes()
					await self.ParentClass.disconnect()

				# finally parse the blob of response
				if debug: ic(self.message_len, self.message_id, self.response)
				await self.messages[self.message_id]()

			except Exception as E:
				print(E)
				breakpoint()

		
	async def parse_keep_alive(self):
		# keep-alive
		message = self.response[:4]
		print(f'Keep-Alive from {self.ParentClass}')
		self.response = self.response[4:]
		
	
	async def parse_choke(self):
		# client got choked by peer
		message = self.response[:5]
		self.response = self.response[5:]
		await self.ParentClass.disconnect(f"Choked client!")
		
		
	async def parse_unchoke(self):
		message = self.response[:5]
		self.ParentClass.choking_me = False
		self.ParentClass.am_interested = True
		print(f"Unchoke from {self.ParentClass}")
		self.response = self.response[5:]
		
		
	async def parse_have(self):
		message = self.response[:9]
		# we just need the piece index so we can ignore the first 5 bytes of message
		# unpack returns tuple. Selecting first element.
		piece_index = unpack('>I', message[5:])[0]
		print(f"Got Have from {self.ParentClass} for piece index {piece_index}")
		self.ParentClass.pieces[piece_index] = True
		self.response = self.response[9:]
		
	
	@staticmethod
	def parse_piece(response):
		message_len = unpack('>I', response[:4])[0]
		message_id = unpack('>B', response[4:5])[0]
		index, offset = unpack('>II', response[5: 13])
		payload = response[13:]
		return (index, offset, payload)
		
		
	async def parse_bitfield(self):
		# Since bitfield len is 1+X. X is length of bitfield
		self.message_len -= 1
		total = self.message_len + self.message_id
		message = self.response[5:total]
		self.ParentClass.handle_bitfield(message)
		print(f"Bitfield from {self.ParentClass}")
		self.response = self.response[total:]
		
		
	async def parse_handshake(self):
		# Total is 68 bytes
		total = 68
		message = self.response[:total]
		await self.ParentClass.handle_handshake(message)
		print(f"Handshake from {self.ParentClass}")
		self.response = self.response[total:]

		

if __name__ == "__main__":
	import asyncio
	async def aioclosure():
		test = bytes()
		await PeerResponseParser.parse(object(), test)
	asyncio.run(aioclosure())