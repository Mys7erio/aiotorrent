import socket
import random
import bencode
import hashlib
import os

# from core.util import chunk
from ipaddress import IPv4Address
from struct import unpack

actual_peers = []

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

def send_get_peers(info_hash, node_id, node_addr):
    print(f"Connecting to peer: {node_addr}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3)

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
    sock.sendto(message, node_addr)

    try:
        data, _ = sock.recvfrom(65536)
        response = bencode.bdecode(data)
        return response
    except socket.timeout:
        print("No response received.")
        return None
    except Exception as e:
        print(e)
    finally:
        sock.close()

def parse_response(response):
    if not response or 'r' not in response:
        return None

    r = response['r']
        # Found peers directly
    if 'values' in r:
        peers = []
        peers_addrs = r['values']
        for peer_addr in peers_addrs:
            ip, port = unpack('>IH', peer_addr)
            ip = IPv4Address(ip).compressed
            peers.append((ip, port))
        breakpoint()
        return [peer for peer in peers]
    elif 'nodes' in r:
        # Got closer nodes (encoded compact format)
        nodes = r['nodes']
        return decode_nodes(nodes)
    return None

def decode_nodes(nodes_blob):
    nodes = []
    # for i in range(0, len(nodes_blob), 26):
    #     nid = nodes_blob[i:i+20]
    #     ip = socket.inet_ntoa(nodes_blob[i+20:i+24])
    #     port = int.from_bytes(nodes_blob[i+24:i+26], 'big')
    #     print(ip, port)
    #     nodes.append((nid, ip, port))

    for node_info in chunk(nodes_blob, 26):
        node_id = node_info[:19]
        ip, port = unpack('>IH', node_info[20:26])
        ip = IPv4Address(ip).compressed
        print(ip, port)
        nodes.append((ip, port))
    return nodes

# --- Example usage ---
node_id = random_node_id()
info_hash = random_info_hash()  # Replace with actual info_hash if needed

nodes = [BOOTSTRAP_NODE]
while len(nodes) > 0:
    node = nodes.pop()
    response = send_get_peers(info_hash, node_id, node)
    results = parse_response(response)
    if results is not None:
        nodes.extend(results)
    else:
        print("Empty result")

print("Results:")
for r in results or []:
    print(r)
