class File:
	#TODO: Rename to TorrentFile
	"""
	{
		'length': int,
		'path': list[str]
	}
	"""
	def __init__(self, file_info: dict, counted: int, piece_size: int) -> None:
		self.size = file_info['length']

		# In case of single file torrent, the name is a string, and not a list of filenames[strings]
		filename = file_info['path']
		self.name = filename[0] if isinstance(filename, list) else filename
		self.__bytes_written = 0
		self.__bytes_downloaded = 0

		start_piece, start_byte = divmod(counted, piece_size)
		end_piece, end_byte = divmod((counted + self.size), piece_size)

		self.start_piece = start_piece
		self.start_byte = start_byte
		self.end_piece = end_piece
		self.end_byte = end_byte


	def __repr__(self):
		return f"{self.name} ({self.size})"
	

	def get_bytes_written(self):
		"""Returns the number of bytes written to disk for the file"""
		return self.__bytes_written


	def _set_bytes_written(self, value):
		self.__bytes_written = value


	def get_bytes_downloaded(self):
		"""
			Returns the number of bytes downloaded for the file, regardless of whether they were written to disk or not.
			Bytes (Pieces) may be discarded if the piece is declared invalid (Piece hash does not match).
		"""
		return self.__bytes_downloaded
	

	def _set_bytes_downloaded(self, value):
		self.__bytes_downloaded = value


	def get_download_progress(self, precision=2):
		"""Convenience function for getting the download progress in percentage"""
		download_progress = (self.__bytes_written / self.size) * 100
		return round(download_progress, precision)


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

