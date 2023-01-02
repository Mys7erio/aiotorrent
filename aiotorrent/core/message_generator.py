from struct import pack


class MessageGenerator:
	"""
		This class generates messages.
	"""
	@staticmethod
	def gen_handshake(info_hash):
		'''
		handshake:
			<pstrlen>	1   byte; string length of <pstr>, as a single raw byte; strlen = 19
			<pstr>		19 bytes; string identifier of the protocol; "BitTorrent protocol"
			<reserved>	8  bytes; eight (8) reserved bytes
			<info_hash>	20 bytes; info_hash
			<peer_id>	20 bytes; peer_id
		'''
		message = pack(
			">B19sQ20s20s",
			19,
			b"BitTorrent protocol",
			00000000,
			info_hash,
			b"ABCD" + b"X"*16			
		)

		return message


	@staticmethod
	def gen_interested():
		mlen, mid = 1, 2
		message = pack(">IB", mlen, mid)
		return message


	@staticmethod
	def gen_request(index, offset, BLOCK_SIZE=(2 ** 14)):
		mlen, mid = 13, 6
		message = pack(">IBIII", mlen, mid, index, offset, BLOCK_SIZE)
		return message