from struct import pack, unpack
from bitstring import BitArray


class PeerResponseHandler:
	def __init__(self, ParentClass):
		self.ParentClass = ParentClass


	async def handshake(self, message):
		if not message or len(message) < 68:
			# if empty or no response, peer is inactive
			# if response is less than 68, wrong response by peer
			await self.ParentClass.disconnect("Empty/None/Wrong handshake message! ")
			return

		pstrlen, pstr, res, info_hash, peer_id = unpack('>B19sQ20s20s', message)

		if pstrlen != 19 or pstr != b"BitTorrent protocol":
			await self.ParentClass.disconnect("Invalid pstrlen or pstr! ")
			return

		handshake_response = {
			"pstrlen": pstrlen,
			"pstr": pstr,
			"reserved": res,
			"info_hash": info_hash,
			"peer_id": peer_id,
		}

		self.ParentClass.has_handshaked = True
		self.ParentClass.handshake_response = handshake_response


	def bitfield(self, message):
		bitfield_message = BitArray(message)
		self.ParentClass.pieces = bitfield_message
		self.ParentClass.has_bitfield = True

