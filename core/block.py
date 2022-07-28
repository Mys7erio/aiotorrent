BLOCK_SIZE = 2 ** 14


class Block:
	def __init__(self, piece_num=-1, offset=-1, data=bytes()):
		self.piece_num = piece_num # Piece which this block belongs to
		self.offset = offset
		self.data = data
		self.num = int(offset / BLOCK_SIZE) # Block index of a particular piece

		if self.data: print(f"Got {self}")


	def __repr__(self):
		return (f"Block #{self.piece_num}-{self.num}")