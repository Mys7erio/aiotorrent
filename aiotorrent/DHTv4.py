import os
import asyncio
import logging
from struct import unpack
from ipaddress import IPv4Address

# import bencode
from aiotorrent.core.bencode_utils import bencode_util
# from bencode._bencode import BTFailure

from aiotorrent.core.util import chunk


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


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
        return bencode_util.bencode(query)


    def _bytes_to_address(self, blob):
        if isinstance(blob, str):
            blob = blob.encode()
        try:
            ip, port = unpack('>IH', blob)
            ip = IPv4Address(ip).compressed
            return (ip, port)
        # except BTFailure as e:
        #     logger.error(f"Invalid IP Address {ip:port}: {e}")
        except Exception as e:
            logger.error(f"An unknown error occured decoding IP Address {ip:port}: {e}")


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
            response = bencode_util.bdecode(response)
            if not response or 'r' not in response:
                return None

            # Found peers directly
            if 'values' in response['r']:
                for peer_addr in response['r']['values']:
                    peers.append(self._bytes_to_address(peer_addr))
            
            if 'nodes' in response['r']:
                closer_nodes_blob = response['r']['nodes']
                closer_nodes.extend(self._decode_nodes(closer_nodes_blob))

        # except BTFailure as e:
        #     logger.error(f"Error decoding bencoded data recieved from peer {peer_addr}: {e}")
        
        except Exception as e:
            logger.error(f"An unknown error occured while parsind bencoded data recieved from {peer_addr}: {e}")

        finally:
            return (peers, closer_nodes)


    async def send_get_peers_req(self, peer_addr, message, loop, _semaphore, timeout=5):
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
            logger.debug(f"Timeout from {peer_addr}")
            return None
        
        except Exception as e:
            logger.error(f"An unknown error occured while sending a datagram to {peer_addr}: {e}")
        
        finally:
            _semaphore.release()


    async def crawl(self, min_peers_to_retrieve = 100, max_connections = 256):
        loop = asyncio.get_running_loop()
        logger.info(f"Starting DHT crawl with Node ID: {self.node_id.hex()}")

        processed_count = 0
        semaphore = asyncio.Semaphore(max_connections)

        while len(self.FOUND_PEERS) < min_peers_to_retrieve:
            if self._nodes_to_crawl.empty():
                logger.info("Exhausted all available nodes on DHT")
                break
            
            await semaphore.acquire()
            peer_addr = await self._nodes_to_crawl.get()
            transaction_id = os.urandom(2)
            message = self._generate_get_peers_query(transaction_id, self.info_hash)
            asyncio.create_task(self.send_get_peers_req(peer_addr, message, loop, semaphore))
            processed_count += 1
            await asyncio.sleep(0.5)

            # Empty queue to check how the program handles an exhausted queue
            # if len(self.FOUND_PEERS) > min_peers_to_retrieve / 2:
            #     while not self._nodes_to_crawl.empty():
            #         self._nodes_to_crawl.get_nowait()

            logger.info(f"Found {len(self.FOUND_PEERS)}/{min_peers_to_retrieve} peers [{self._nodes_to_crawl.qsize()} in queue]")

        logger.info(f"Found {len(self.FOUND_PEERS)} peers after crawling {processed_count} nodes")
        logger.debug(f"{self._nodes_to_crawl.qsize()} nodes left in queue")
        
        return self.FOUND_PEERS
        

if __name__ == "__main__":
    INFO_HASH = b""
    node_id = os.urandom(20)

    dht_crawler = SimpleDHTCrawler(INFO_HASH, node_id)
    asyncio.run(dht_crawler.crawl())