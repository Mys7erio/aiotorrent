from pathlib import Path


BLOCK_SIZE = 2 ** 14


class Block:
	def __init__(self, piece_num=-1, offset=-1, data=bytes()):
		self.piece_num = piece_num # Piece which this block belongs to
		self.offset = offset
		self.data = data
		self.num = int(offset / BLOCK_SIZE) # Block index of a particular piece


	def __repr__(self):
		return (f"Block #{self.piece_num}-{self.num}")



class PieceWriter:
	def __init__(self, directory_name, file):
		self.file = file
		self.directory = directory_name
		# Create a directory with the same name as torrent name to download files to
		Path(self.directory).mkdir(exist_ok=True)


	def __enter__(self):
		filepath = f"{self.directory}/{self.file.name}"
		self.target_file = open(filepath, 'ab')
		return self


	def write(self, piece):
		# Zero based index of piece within the file
		piece_index = piece.piece_num - self.file.start_piece
		offset = piece_index * piece.piece_size
		self.target_file.seek(offset)
		self.target_file.write(piece.data)
		print(f"Wrote {piece} to {self.file.name}")


	def __exit__(self, exc_type, exc_value, exc_traceback):
		self.target_file.close()



def chunk(string, size):
	"""A function that splits a string into specified chunk size

		string: str
			The string to be broken / chunked down
		size: int
			The size of each chunk
	"""

	for _ in range(0, len(string), size):
		yield string[:size]
		string = string[size:]


	

if __name__ == "__main__":
	a = 'abcabcabcabcabcabcabcabcabcabc'
	for i in chunk(a, 7):
		print(i)