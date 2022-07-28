from struct import pack, unpack
from bitstring import BitArray


from core.block import Block


class PeerResponseHandler:
	def __init__(self, artifacts, Peer=None):
		self.artifacts = artifacts
		self.Peer = Peer

	async def handle(self, _debug=False):
		if _debug: [print(key, len(value)) for key, value in self.artifacts.items()]

		while self.artifacts:
			if "keep_alive" in self.artifacts: self.handle_keep_alive() 
			if "choke" in self.artifacts: await self.handle_choke()
			if "unchoke" in self.artifacts: self.handle_unchoke()
			if "handshake" in self.artifacts: await self.handle_handshake()
			# Merged have_handler into bitfield_handler
			if "have" in self.artifacts: self.handle_bitfield()
			if "bitfield" in self.artifacts: self.handle_bitfield()
			# Piece handler is special as it returns values
			if "piece" in self.artifacts: return self.handle_piece()



	def handle_keep_alive(self):
		print(f'Keep-Alive from {self.Peer}')
		self.artifacts.pop('keep_alive')


	async def handle_choke(self):
		await self.Peer.disconnect(f"Choked client!")
		self.artifacts.pop('choke')


	def handle_unchoke(self):
		self.Peer.choking_me = False
		self.Peer.am_interested = True
		print(f"Unchoke from {self.Peer}")
		self.artifacts.pop('unchoke')


	async def handle_handshake(self):
		message = self.artifacts['handshake']
		if not message or len(message) < 68:
			# if empty or no response, peer is inactive
			# if response is less than 68, wrong response by peer
			await self.Peer.disconnect("Empty/None/Wrong handshake message! ")

		pstrlen, pstr, res, info_hash, peer_id = unpack('>B19sQ20s20s', message)

		if pstrlen != 19 or pstr != b"BitTorrent protocol":
			await self.Peer.disconnect("Invalid pstrlen or pstr! ")

		handshake_response = {
			"pstrlen": pstrlen,
			"pstr": pstr,
			"reserved": res,
			"info_hash": info_hash,
			"peer_id": peer_id,
		}

		self.Peer.has_handshaked = True
		self.Peer.handshake_response = handshake_response

		print(f"Handshake from {self.Peer}")
		self.artifacts.pop('handshake')


	def handle_bitfield(self):
		# Create bitfield from bitfield message if available
		# If not available, create empty bitfield_message
		if 'bitfield' in self.artifacts:
			message = self.artifacts['bitfield']
			pieces = BitArray(message)
		else:
			num_pieces = len(self.Peer.torrent_info['piece_hashmap'])
			pieces = BitArray(num_pieces)

		# Merge have requests if available
		if 'have' in self.artifacts:
			for piece_num in self.artifacts['have']:
				pieces[piece_num] = True

		# Finally set Peer pieces value to local pieces value
		self.Peer.pieces = pieces
		try:
			self.artifacts.pop('have')
			self.artifacts.pop('bitfield')
		except KeyError:
			...
		finally:
			print(f"Bitfield from {self.Peer}")


	def handle_piece(self):
		# This is the only method which returns any value
		try:
			index, offset, data = self.artifacts['piece']
			block = Block(index, offset, data)
			return block
		except TypeError:
			raise TypeError(f"Handler: Failed To Extract Piece sent by {self.Peer}")
		finally:
			self.artifacts.pop('piece')



if __name__ == "__main__":
	import asyncio
	artifacts = dict()
	index = 0
	offset = 376832
	with open('utils/piece.txt', 'rb') as file:
		data = file.read()

	artifacts['piece'] = (index, offset, data)

	async def f():
		idontknow = await PeerResponseHandler(artifacts).handle()
		print(idontknow)

	asyncio.run(f())