"""
A basic non-caching proxy.

Features:
* multi-process architecture

Architecture:
* one listener listens on a port and places requests on a request queue
* one or more connect workers make the connections
* several workers forward the packets. One worker can serve multiple connections.

"""
import sys
import socket
import signal

from multiprocessing import Process, JoinableQueue

from net import Socket, Endpoint
from workers import SwitchWorker, TunnelWorker, ProxyWorker

LISTEN_ADDRESS = '127.0.0.1'
LISTEN_PORT = 8888

running = True

def signalHandler(signum, frame):
	global running
	print("Received %d signal from %s" % (signum, frame))
	if signum == signal.SIGTERM:
		running = False
		print("Quiting")


def main():
	signal.signal(signal.SIGTERM, signalHandler)

	connectRequestsQueue = JoinableQueue(20)
	forwardingQueue = JoinableQueue(20)
	proxyingQueue = JoinableQueue(20)

	processes = []
	print("Starting workers...")
	workers = [ SwitchWorker("Adam", connectRequestsQueue, forwardingQueue, proxyingQueue),
				TunnelWorker("Ted", forwardingQueue),
				ProxyWorker("Perseus", proxyingQueue),
				ProxyWorker("Penelope", proxyingQueue),
			]
	for worker in workers:
		p = Process(target=worker.work, args=())
		processes.append(p)
		p.start()

	listeningSocket = Socket(socket.AF_INET, socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
	listeningSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	listeningSocket.bind((LISTEN_ADDRESS, LISTEN_PORT))
	listeningSocket.listen(10)

	try:
		while running:
			clientSocket, clientAddress = listeningSocket.accept()
			client = Endpoint(clientSocket, clientAddress)
			connectRequestsQueue.put(client.reduce())
	except KeyboardInterrupt:
		print("Quitting... requested by user")
	finally:
		listeningSocket.close()

	#wait for all of the child processes
	# TODO: should stop the processes if quitting not user requested
	print("Waiting for child processes...")
	for p in processes:
		p.join()
	print("Done!")

	return 0

if __name__ == "__main__":
	sys.exit(main())




