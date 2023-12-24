import logging
from struct import unpack
from struct import error as UnpackError


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class PeerResponseParser:
	def __init__(self, response):
		self.response = response
		
		self.messages = {
		# self created index. Does not necessarily follow bittorrent protocol specification
			0: self.parse_choke,
			1: self.parse_unchoke,
			4: self.parse_have,
			5: self.parse_bitfield,
			7: self.parse_piece,
			19: self.parse_handshake,
			None: self.parse_keep_alive
		}
		self.artifacts = dict()


	def parse(self):

		while self.response:
			try:
				# if first byte of response is 19 bytes, it's a handshake
				if self.response[0] == 19:
					self.parse_handshake()
					continue #	issue #1

				# message len and id need to be class wide accessible because message len
				# needs to be updated in case of a bitfield and piece requests
				self.message_len = unpack('>I', self.response[:4])[0]
				self.message_id = unpack('>B', self.response[4:5])[0] if self.message_len != 0 else None
					
				# keep-alive messages have length 0 and no message_id
				if self.message_len == 0 and not self.message_id: self.parse_keep_alive()

				# if msg id not in message index, clear response
				if self.message_id not in self.messages:
					logger.warning(f"{self.message_id=}, {self.message_len=}, {self.response[:16]}")
					self.response = bytes()

				# finally parse the blob of response
				logger.debug(f"{self.message_len=}, {self.message_id=}, {self.response[:16]=}")
				self.messages[self.message_id]()

			# In case of general exception, clear the response
			except Exception as E:
				logger.warning(f"Parser: {E}")
				self.response = bytes()
			
		return self.artifacts

		
	def parse_keep_alive(self):
		# keep-alive
		message = self.response[:4]
		self.response = self.response[4:]
		self.artifacts.update({'keep_alive': True})
		
	
	def parse_choke(self):
		# client got choked by peer
		message = self.response[:5]
		self.response = self.response[5:]
		self.artifacts.update({'choke': True})
		
		
	def parse_unchoke(self):
		message = self.response[:5]
		self.response = self.response[5:]
		self.artifacts.update({'unchoke': True})
		
		
	def parse_have(self):
		message = self.response[:9]
		# We just need the piece index so we can ignore the first 5 bytes of message.
		# Unpack returns tuple , selecting first element.
		piece_index = unpack('>I', message[5:])[0]
		self.response = self.response[9:]
		self.artifacts.update({'have': {piece_index: True}})
		
	
	def parse_piece(self):
		# Returns index, offset and block except when there's
		# an unpack error. In the second case, It raises a TypeError
		if not 'pieces' in self.artifacts: self.artifacts['pieces'] = list()
		block_len = self.message_len - 9
		total = block_len + 13
		try:
			index, offset = unpack('>II', self.response[5: 13])
			data = self.response[13:total]
			block_info = (index, offset, data)
			self.artifacts['pieces'].append(block_info)
		except UnpackError:
			raise TypeError("Parser: Failed to extract piece")
		finally:
			self.response = self.response[total:]
		
		
	def parse_bitfield(self):
		# Since bitfield len is 1+X. X is length of bitfield
		self.message_len -= 1
		total = self.message_len + self.message_id
		message = self.response[5:total]
		self.response = self.response[total:]
		self.artifacts.update({'bitfield': message})
		
		
	def parse_handshake(self):
		# Total is 68 bytes
		total = 68
		message = self.response[:total]
		self.response = self.response[total:]
		self.artifacts.update({'handshake': message})

		

if __name__ == "__main__":
	...