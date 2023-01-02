from urllib.parse import urlparse

from aiotorrent.core.trackers import UDPTracker, HTTPTracker, WSSTracker


class TrackerFactory:
	"""
	Using factory method to return the type of tracker required
	"""
	def __new__(self, tracker_addr, torrent_info):

		tracker_types = {
			'udp': UDPTracker,
			'wss': WSSTracker,
			'http': HTTPTracker,
			'https': HTTPTracker,
		}

		t_type = urlparse(tracker_addr).scheme
		return tracker_types[t_type](tracker_addr, torrent_info)