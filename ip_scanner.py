from io import TextIOWrapper
import os
import argparse
import time
from threading import Lock, Thread
from queue import Queue
from random import shuffle

from util import minecraft_util, scanning_util


rangeQueue: Queue = Queue()
sockQueue: Queue = Queue()

SOCKET_TIMEOUT_SECS = 0.6
DEFAULT_THREADS = 3
DEFAULT_SOCKETS = 256


def scanSock(timedSock: scanning_util.TimedSocket, outputFile: TextIOWrapper, fileLock: Lock) -> None:

    """
    Ask a succesfully connected socket for the Server List and then try
    to process it
    """

    serverInfoJson: dict = {}
    buffer = b''

    # Ask for Server List
    try:
        minecraft_util.serverListPing(timedSock.sock, timedSock.ip, timedSock.port)
        minecraft_util.statusRequest(timedSock.sock)
    except:
        pass

    # Receive Server list
    timedSock.restartTimer()

    while timedSock.getTimePassedSeconds() < 7:         # We want to give the socket enough time
        try:
            buffer += timedSock.sock.recv(4096)
        except:
            pass

    if buffer == b'':
        return                                          # Return if no information was received

    # Decode Server List Packet
    try:
        serverInfoJson = minecraft_util.decodeStatusResponse(buffer)
    except:
        print("")
        print(timedSock.ip + " : Error decoding the packet")
        print("")
        return

    # Write Server List info to file
    scanning_util.writeServerToFileLock(timedSock.ip, serverInfoJson, outputFile, fileLock)


def checkSocketsThread(outputFile: TextIOWrapper, fileLock: Lock) -> None:

    """
    Will check the sockets and if one is connected, it will ask for the Server List
    If a socket times out, it will be removed
    I don't like the implementations but it is what it is
    """

    while True:
        if not sockQueue.empty():
            timedSock: scanning_util.TimedSocket = sockQueue.get()

            if timedSock.isConnected():
                scanSock(timedSock, outputFile, fileLock)
                timedSock.sock.close()
                continue

            if timedSock.getTimePassedSeconds() > SOCKET_TIMEOUT_SECS:
                timedSock.sock.close()
                continue

            # If socket is not connected and it has not timedout, put it back in queue
            sockQueue.put(timedSock)


def addSocketsToQueue(maxSocks: int, scannedIpsFile: TextIOWrapper) -> None:

    """
    Creates sockets, tries to connect them to an ip and
    adds them to the queue
    """

    while not rangeQueue.empty():
        ipRange: tuple = rangeQueue.get()
        print(f"Scanning: {ipRange[0]}.{ipRange[1]}.0.0")

        for X in range(256):

            for Y in range(256):
                while sockQueue.qsize() > maxSocks:
                    pass

                ip = f"{ipRange[0]}.{ipRange[1]}.{X}.{Y}"
                timedSock = scanning_util.TimedSocket(ip, minecraft_util.DEFAULT_PORT)
                sockQueue.put(timedSock)

        scannedIpsFile.write(f"{ipRange[0]}.{ipRange[1]}.0.0\n")        # Add them to the file so that the range wont be checked again


def buildRangeQueue(fileName: str, scannedIps: list) -> None:

    """
    If no file is provided, we want to scan the whole internet
    If a file was provided, we only scan the ranges included in the file
    Always check if the range was already scanned
    """

    # No file provided
    if fileName == None:

        # Scan the whole internet
        for A in range(256):
            for B in range(256):

                # Check if range has already been scanned
                if scanning_util.rangeAlreadyScanned(scannedIps, f"{A}.{B}.0.0"):
                    continue

                rangeQueue.put((A, B))
        return
    
    # Ips-to-scan file provided
    with open(fileName, "r") as file:
        ipsToScan = file.read().splitlines()
        for ip in ipsToScan:

            if scanning_util.rangeAlreadyScanned(scannedIps, ip):
                continue

            ipSplit = ip.split(".")
            rangeQueue.put((ipSplit[0], ipSplit[1]))


def parseArguments(parser: argparse.ArgumentParser) -> argparse.Namespace:
    parser.add_argument("-t", "--threads",
                        type=int, default=DEFAULT_THREADS,
                        help="Number of Threads to be used to scan the sockets")

    parser.add_argument("-s", "--sockets",
                        type=int, default=DEFAULT_SOCKETS,
                        help="Number of sockets to be used to scan the internet")

    parser.add_argument("-i", "--ips",
                        help="File that contains ip ranges to scan (if no file is provided, it will scan the whole internet)")

    return parser.parse_args()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    args = parseArguments(parser)

    # Save scan results to new file
    os.makedirs("results", exist_ok=True)
    os.makedirs("results/scans", exist_ok=True)

    fileName = f"results/scans/{time.strftime('%Y%m%d-%H%M%S')}.txt"
    scannedIpsName = f"results/scanned_ips.txt"


    print("")
    print("-----------------------------------------------")
    print("TheF1xer's Minecraft Server Scanner")
    print("Saving results to file: " + fileName)
    print("")
    print("Using " + str(args.sockets) + " threads")
    print("and " + str(args.threads) + " non-blocking sockets")
    print("-----------------------------------------------")
    print("")


    # This is where the fun starts
    with open(fileName, "w") as outputFile, open(scannedIpsName, "a+") as scannedIpsFile:
        fileLock = Lock()
        scannedIps = scanning_util.getScannedIps(scannedIpsFile)

        """
        This is where the Range Queue is filed with ips that have not been scanned.
        The ip ranges that have been scanned are stored in the scannedIpsFile
        """

        buildRangeQueue(args.ips, scannedIps)
    
        shuffle(rangeQueue.queue)       # Shuffling is more fun

        """
        Threads are build and started. The threads will check the sockets and try to get
        the Server List
        """

        for i in range(args.threads):
            t = Thread(target=checkSocketsThread, args=(outputFile, fileLock))
            t.daemon = True
            t.start()
    
        """
        The main thread will create the sockets and connect them to "random" ips, if they
        are succesfully connected, the connection will be checked by the threads
        """

        addSocketsToQueue(args.sockets, scannedIpsFile)
        
