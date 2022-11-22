class PeersManager:
	def __init__(self, peer_list):
		self.peer_list = peer_list
		self.peers_selected = list()
		self.black_list = list()


	def dispatch(self, piece_num):
		for peer in self.peers_selected:
			ip, port = peer.address
			if not ip in self.black_list:
				if peer.pieces[piece_num]:
					# peer.busy = True
					self.peers_selected.remove(peer)
					return peer
		# Raise ValueError if no peers are available
		raise ValueError("No Peers Available")


	def retrieve(self, peer):
		# peer.busy = False
		self.peer_list.append(peer)


	def peers_available(self, piece_num):
		for peer in self.peer_list:
			ip, port = peer.address
			if not ip in self.black_list:
				if peer.pieces[piece_num]:
					self.peers_selected.append(peer)
					self.peer_list.remove(peer)
					return True
		return False


	# def blacklist(self, ip):
	# 	self.black_list.append(ip)


	# async def hailmary(self, message):
	# 	for peer in self.peer_list:
	# 		try:
	# 			response = await peer.send_message(message)
	# 			if response: breakpoint()
	# 		except BrokenPipeError:
	# 			peer.active = False

