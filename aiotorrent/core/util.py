import asyncio
import logging
from enum import Enum
from pathlib import Path


BLOCK_SIZE = 2 ** 14
MIN_BLOCKS_PER_CYCLE = 8
BLOCKS_PER_CYCLE = MIN_BLOCKS_PER_CYCLE

class DownloadStrategy(Enum):
	DEFAULT = 0
	SEQUENTIAL = 10


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


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
		self.target_file = open(filepath, 'wb')
		return self


	def write(self, piece):
		# Zero based index of piece within the file
		piece_index = piece.num - self.file.start_piece

		# Calculate offset of piece within the file
		# Reduce file.start_byte from offset in case the file does not start at offset 0 of the piece.
		# In other words, the piece has parts of more than one file.
		offset = (piece_index * piece.piece_size) - self.file.start_byte

		# A negative offset means that this piece contained data for other files
		# Reset offset to 0 in case of a negative offset
		if offset < 0: offset = 0

		# Move the file pointer to the correct offset and write the piece data
		self.target_file.seek(offset)
		self.target_file.write(piece.data)
		logger.info(f"Wrote {piece} to {self.file.name}")


	def __exit__(self, exc_type, exc_value, exc_traceback):
		self.target_file.close()



def chunk(string, size):
	"""A function that splits a string into specified chunk size

		string: str
			The string to be broken / chunked down
		size: int
			The size of each chunk
	"""
	# Use the built-in slice function
	for _ in range(0, len(string), size):
		yield string[:size]
		string = string[size:]



class SequentialPieceDispatcher:
	MEMORY_LIMIT = 1024 * 1024  * 64 # 64MB
	pieces_queue = asyncio.PriorityQueue()
	_pieces_in_queue = 0
	_file_piece_size = 0


	def __init__(self, file, piece_len) -> None:
		self.current = file.start_piece
		self.end = file.end_piece
		self._file_piece_size = piece_len


	async def put(self, piece) -> None:
		queue_size = self.pieces_queue.qsize() * self._file_piece_size
		if queue_size > self.MEMORY_LIMIT:
			raise MemoryError("Memory limit exceeded")
		else:
			await self.pieces_queue.put((piece.num, piece))
			self._pieces_in_queue += 1


	async def dispatch(self):
		while not self.pieces_queue.empty():
			priority, piece = await self.pieces_queue.get()
			if piece.num != self.current:
				self.pieces_queue.put_nowait((priority, piece))
				break
			else:
				self.current += 1
				yield piece


	async def drain(self):
		while not self.pieces_queue.empty():
			_, piece = await self.pieces_queue.get()
			yield piece
