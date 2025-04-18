import asyncio
import os
from struct import unpack
import bencode
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
    return bencode.bencode(query)

def convert_blob_to_address(blob):
    try:
        ip, port = unpack('>IH', blob)
        ip = IPv4Address(ip).compressed
        return (ip, port)
    except Exception as e:
        breakpoint()

def decode_nodes(nodes_blob):
    nodes = []
    for node_info in chunk(nodes_blob, 26):
        node_id = node_info[:19]
        node_ip, node_port = convert_blob_to_address(node_info[20:26])
        # I mean do we really need the node_id?
        nodes.append((node_ip, node_port))
    
    return nodes


def parse_response(response):
    peers = []
    closer_nodes = []
    response = bencode.bdecode(response)
    if not response or 'r' not in response:
        return None

    # Found peers directly
    if 'values' in response['r']:
        for peer_addr in response['r']['values']:
            # ip, port = unpack('>IH', peer_addr)
            # ip = IPv4Address(ip).compressed
            peers.append(convert_blob_to_address(peer_addr))
    
    if 'nodes' in response['r']:
        closer_nodes_blob = response['r']['nodes']
        closer_nodes.extend(decode_nodes(closer_nodes_blob))
        # return decode_nodes(nodes)
    
    # breakpoint()
    return (peers, closer_nodes)


class DHTClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, message, on_response, on_error=None):
        self.message = message
        self.on_response = on_response
        self.on_error = on_error or (lambda e: None)

    def connection_made(self, transport):
        self.transport = transport
        self.transport.sendto(self.message)

    def datagram_received(self, data, addr):
        self.on_response(data)
        self.transport.close()

    def error_received(self, exc):
        self.on_error(exc)
        self.transport.close()

    def connection_lost(self, exc):
        pass  # Optional: handle cleanup


async def send_get_peers_req(peer_addr, message, loop, timeout=5):
    response_future = loop.create_future()

    def on_response(data):
        peers, closer_nodes = parse_response(data)
        if peers:
            breakpoint()
        for node in closer_nodes:
            NODES.put_nowait(node)
        if not response_future.done():
            response_future.set_result(data)

    def on_error(exc):
        if not response_future.done():
            response_future.set_exception(exc)

    await loop.create_datagram_endpoint(
        lambda: DHTClientProtocol(message, on_response, on_error),
        remote_addr=peer_addr
    )

    try:
        return await asyncio.wait_for(response_future, timeout)
    except asyncio.TimeoutError:
        print(f"Timeout from {peer_addr}")
        return None




# --- Example usage ---
async def main():
    loop = asyncio.get_running_loop()
    while not NODES.empty():
        iteration = 0
        
        message = gen_get_peers_query(os.urandom(2), INFO_HASH)
        peer_addr = await NODES.get()
        response = await send_get_peers_req(peer_addr, message, loop)
        

if __name__ == "__main__":
    asyncio.run(main())
