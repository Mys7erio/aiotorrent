import asyncio
import os
from struct import unpack
from ipaddress import IPv4Address



INFO_HASH = b"\xdd\x82U\xec\xdc|\xa5_\xb0\xbb\xf8\x13#\xd8pb\xdb\x1fm\x1c"


NODE_ID = os.urandom(20)
BOOTSTRAP_NODES = [
    ('router.bittorrent.com', 6881)
]

NODES = asyncio.PriorityQueue()
for node in BOOTSTRAP_NODES:
    NODES.put_nowait(node)



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



def gen_get_peers_query(transaction_id, info_hash):
    query = {
        b't': transaction_id,
        b'y': b'q',
        b'q': b'get_peers',
        b'a': {
            b'id': NODE_ID,
            b'info_hash': info_hash
        }
    }

def convert_blob_to_address(blob):
    ip, port = unpack('>IH', blob)
    ip = IPv4Address(ip).compressed
    return (ip, port)

def decode_nodes(nodes_blob):
    nodes = []
    for node_info in chunk(nodes_blob, 26):
        node_id = node_info[:19]
        node_ip, node_port = convert_blob_to_address(node[20:26])
        # I mean do we really need the node_id?
        nodes.apped((node_ip, node_port))
    
    return nodes


def parse_response(response):
    peers = []
    if not response or 'r' not in response:
        return None
    breakpoint()
    # Found peers directly
    if 'values' in response['r']:
        for peer_addr in response['r']['values']:
            # ip, port = unpack('>IH', peer_addr)
            # ip = IPv4Address(ip).compressed
            peers.append(convert_blob_to_address(peer_addr))

    elif 'nodes' in response['r']['values']:
        nodes = response['r']['nodes']
        return decode_nodes(nodes)
    return None


class DHTClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, message, on_response):
        breakpoint()
        self.message = message
        self.on_response = on_response

    def connection_made(self, transport):
        self.transport = transport
        self.transport.sendto(self.message)

    def datagram_received(self, data, addr):
        breakpoint()
        self.on_response.set_result((data, addr))

    def error_received(self, exc):
        self.on_response.set_exception(exc)

    def connection_lost(self, exc):
        pass  # Optional: handle cleanup


async def send_get_peers_req(peer_addr, message,  loop, timeout = 5):
    ip, port = peer_addr
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: DHTClientProtocol(message, parse_response),
        remote_addr=(ip, port)
    )

    try:
        response = await asyncio.wait_for(on_response, timeout)
        return response
    except asyncio.TimeoutError:
        print("No response received within timeout")
        return None
    finally:
            transport.close()



# --- Example usage ---
async def main():
    loop = asyncio.get_running_loop()
    while not NODES.empty():
        iteration = 0
        
        message = gen_get_peers_query(os.urandom(2), INFO_HASH)
        peer_addr = await NODES.get()
        response = await send_get_peers_req(peer_addr, message, loop)
        breakpoint()

if __name__ == "__main__":
    asyncio.run(main())
