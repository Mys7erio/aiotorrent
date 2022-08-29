class File:
	"""
	{
		'length': int,
		'path': list[str]
	}
	"""
	def __init__(self, file_info: dict, counted: int, piece_size: int) -> None:
		self.size = file_info['length']
		self.name = file_info['path'][0]

		start_piece, start_byte = divmod(counted, piece_size)
		end_piece, end_byte = divmod((counted + self.size), piece_size)

		self.start_piece = start_piece
		self.start_byte = start_byte
		self.end_piece = end_piece
		self.end_byte = end_byte


	def __repr__(self):
		return f"{self.name} ({self.size})"


class FileTree(list):
	"""
	FileTree inherits from list class making FileTree objects
	an iterator as well as making them subscriptable.
	"""
	def __init__(self, torrent_info: dict) -> None:
		counted = 0
		piece_size = torrent_info['piece_len']

		# If it is a single file torrent, create a dictionary in a torrent format
		if not isinstance(torrent_info['files'], list):
			file = {
				'path': torrent_info['files'],
				'length': torrent_info['size'],
			}
			self.append(File(file, counted, piece_size))
			return

		# Create file object for every file in the torrent.
		# Increase the value of the counted var by length of each file.
		for file in torrent_info['files']:
			self.append(File(file, counted, piece_size))
			counted += file['length']

