import asyncio
import os
from struct import unpack
import bencode
from ipaddress import IPv4Address
from bencode._bencode import BTFailure


INFO_HASH = b"\xdd\x82U\xec\xdc|\xa5_\xb0\xbb\xf8\x13#\xd8pb\xdb\x1fm\x1c"
FOUND_PEERS = set()

NODE_ID = os.urandom(20)
BOOTSTRAP_NODES = [
    ('router.bittorrent.com', 6881)
]

NODES = asyncio.LifoQueue()
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
    if isinstance(blob, str):
        blob = blob.encode()
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
    try:
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
    except BTFailure as e:
        # breakpoint()
        print(f"Error decoding bencode: {e}")
    except Exception as e:
        print(f"Error while parsing peer response: {e}")
    finally:
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
            FOUND_PEERS  |= set(peers)

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
    print(f"Starting DHT crawl with Node ID: {NODE_ID.hex()}")

    processed_count = 0
    MAX_NODES_TO_QUERY = 250
    BATCH_SIZE = 25

    while not NODES.empty() and processed_count < MAX_NODES_TO_QUERY:
        nodes_to_process_batch = []
        for _ in range(BATCH_SIZE):
            if not NODES.empty():
                nodes_to_process_batch.append(await NODES.get())
            else:
                break

        if not nodes_to_process_batch:
            break

        print(f"Processing batch of {len(nodes_to_process_batch)} nodes. Queue size: {NODES.qsize()}")

        async with asyncio.TaskGroup() as tg:
            for peer_addr in nodes_to_process_batch:
                transaction_id = os.urandom(2)
                message = gen_get_peers_query(transaction_id, INFO_HASH)
                tg.create_task(send_get_peers_req(peer_addr, message, loop))
                processed_count += 1

        await asyncio.sleep(0.5)

    print(FOUND_PEERS)
    breakpoint()
    print(f"Finished crawling after processing {processed_count} nodes.")
    print(f"Final NODES queue size: {NODES.qsize()}")
        

if __name__ == "__main__":
    asyncio.run(main())
