import socket
import random
import bencode
import hashlib
import os

# from core.util import chunk
from ipaddress import IPv4Address
from struct import unpack

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

BOOTSTRAP_NODE = ('router.bittorrent.com', 6881)

# Generate random 20-byte node ID
def random_node_id():
    return os.urandom(20)

# Example info_hash (replace with actual torrent hash if needed)
def random_info_hash():
    return b"\xdd\x82U\xec\xdc|\xa5_\xb0\xbb\xf8\x13#\xd8pb\xdb\x1fm\x1c"
    # return hashlib.sha1(b"example").digest()

def send_get_peers(info_hash, node_id):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    transaction_id = os.urandom(2)

    query = {
        b't': transaction_id,
        b'y': b'q',
        b'q': b'get_peers',
        b'a': {
            b'id': node_id,
            b'info_hash': info_hash
        }
    }

    message = bencode.bencode(query)
    sock.sendto(message, BOOTSTRAP_NODE)

    try:
        data, _ = sock.recvfrom(65536)
        response = bencode.bdecode(data)
        return response
    except socket.timeout:
        print("No response received.")
        return None
    finally:
        sock.close()

def parse_response(response):
    if not response or 'r' not in response:
        return None

    r = response['r']
    if 'values' in r:
        # Found peers directly
        peers = r['values']
        return [peer for peer in peers]
    elif 'nodes' in r:
        # Got closer nodes (encoded compact format)
        nodes = r['nodes']
        return decode_nodes(nodes)
    return None

def decode_nodes(nodes_blob):
    nodes = []
    for i in range(0, len(nodes_blob), 26):
        nid = nodes_blob[i:i+20]
        ip = socket.inet_ntoa(nodes_blob[i+20:i+24])
        port = int.from_bytes(nodes_blob[i+24:i+26], 'big')
        print(ip, port)
        nodes.append((nid, ip, port))

    for node_info in chunk(nodes_blob, 26):
        node_id = node_info[:19]
        ip, port = unpack('>IH', node_info[20:26])
        ip = IPv4Address(ip).compressed
        print(ip, port)
    return nodes

# --- Example usage ---
node_id = random_node_id()
info_hash = random_info_hash()  # Replace with actual info_hash if needed

response = send_get_peers(info_hash, node_id)
results = parse_response(response)

print("Results:")
for r in results or []:
    print(r)
