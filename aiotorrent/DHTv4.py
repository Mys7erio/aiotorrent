import asyncio
import os
from struct import unpack
import bencode
from ipaddress import IPv4Address
from bencode._bencode import BTFailure

from aiotorrent.core.util import chunk


class DHTProtocolHelper(asyncio.DatagramProtocol):
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


class SimpleDHTCrawler:
    FOUND_PEERS = set()
    _nodes_to_crawl = asyncio.LifoQueue()

    def __init__(self, info_hash, node_id = None, bootstrap_nodes = []):
        self.node_id = node_id or os.urandom(20)
        self.info_hash = info_hash

        self.bootstrap_nodes = bootstrap_nodes or  [
            ('router.bittorrent.com', 6881),
            ('router.utorrent.com', 6881),
            ('trdht.transmissionbt.com', 6881),
        ]

        for node in self.bootstrap_nodes:
            self._nodes_to_crawl.put_nowait(node)


    def _generate_get_peers_query(self, transaction_id, info_hash):
        query = {
            b't': transaction_id,
            b'y': b'q',
            b'q': b'get_peers',
            b'a': {
                b'id': self.node_id,
                b'info_hash': info_hash
            }
        }
        return bencode.bencode(query)


    def _bytes_to_address(self, blob):
        if isinstance(blob, str):
            blob = blob.encode()
        try:
            ip, port = unpack('>IH', blob)
            ip = IPv4Address(ip).compressed
            return (ip, port)
        except BTFailure as e:
            print(e)
        except Exception as e:
            print(e)


    def _decode_nodes(self, nodes_blob):
        nodes = []
        for node_info in chunk(nodes_blob, 26):
            node_id = node_info[:19]
            node_ip, node_port = self._bytes_to_address(node_info[20:26])
            # I mean do we really need the node_id?
            nodes.append((node_ip, node_port))
        
        return nodes


    def parse_response(self, response):
        peers = []
        closer_nodes = []
        try:
            response = bencode.bdecode(response)
            if not response or 'r' not in response:
                return None

            # Found peers directly
            if 'values' in response['r']:
                for peer_addr in response['r']['values']:
                    peers.append(self._bytes_to_address(peer_addr))
            
            if 'nodes' in response['r']:
                closer_nodes_blob = response['r']['nodes']
                closer_nodes.extend(self._decode_nodes(closer_nodes_blob))

        except BTFailure as e:
            print(f"Error decoding bencode: {e}")
        
        except Exception as e:
            print(f"Error while parsing peer response: {e}")

        finally:
            return (peers, closer_nodes)


    async def send_get_peers_req(self, peer_addr, message, loop, timeout=5):
        response_future = loop.create_future()

        def on_response(data):
            peers, closer_nodes = self.parse_response(data)
            if peers:
                self.FOUND_PEERS  |= set(peers)

            for node in closer_nodes:
                self._nodes_to_crawl.put_nowait(node)
            if not response_future.done():
                response_future.set_result(data)

        def on_error(exc):
            if not response_future.done():
                response_future.set_exception(exc)

        try:
            await loop.create_datagram_endpoint(
                lambda: DHTProtocolHelper(message, on_response, on_error),
                remote_addr=peer_addr
            )
            return await asyncio.wait_for(response_future, timeout)
        except asyncio.TimeoutError:
            print(f"Timeout from {peer_addr}")
            return None
        
        except Exception as e:
            print(e)


    async def crawl(self, MAX_NODES_TO_QUERY = None, BATCH_SIZE = None):
        loop = asyncio.get_running_loop()
        print(f"Starting DHT crawl with Node ID: {self.node_id.hex()}")

        processed_count = 0
        MAX_NODES_TO_QUERY = MAX_NODES_TO_QUERY or 250
        BATCH_SIZE = BATCH_SIZE or 25

        while not self._nodes_to_crawl.empty() and processed_count < MAX_NODES_TO_QUERY:
            nodes_to_process_batch = []
            for _ in range(BATCH_SIZE):
                if not self._nodes_to_crawl.empty():
                    nodes_to_process_batch.append(await self._nodes_to_crawl.get())
                else:
                    break

            if not nodes_to_process_batch:
                break

            print(f"Processing batch of {len(nodes_to_process_batch)} nodes. Queue size: {self._nodes_to_crawl.qsize()}")

            async with asyncio.TaskGroup() as tg:
                for peer_addr in nodes_to_process_batch:
                    transaction_id = os.urandom(2)
                    message = self._generate_get_peers_query(transaction_id, self.info_hash)
                    tg.create_task(self.send_get_peers_req(peer_addr, message, loop))
                    processed_count += 1

            await asyncio.sleep(0.5)


        print(self.FOUND_PEERS)
        print(f"Finished crawling after processing {processed_count} nodes.")
        print(f"Final NODES queue size: {self._nodes_to_crawl.qsize()}")
        
        return self.FOUND_PEERS
        

if __name__ == "__main__":
    INFO_HASH = b""
    node_id = os.urandom(20)

    dht_crawler = SimpleDHTCrawler(INFO_HASH, node_id)
    asyncio.run(dht_crawler.crawl())