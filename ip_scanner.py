from io import TextIOWrapper
import os
import sys
import time
from threading import Lock, Thread
from queue import Queue
from random import shuffle

from util import minecraft_util, scanning_util


rangeQueue: Queue = Queue()
sockQueue: Queue
SOCKET_TIMEOUT_SECS = 0.6


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

    while timedSock.getTimePassedSeconds() < 10:         # We want to give the socket enough time
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


if __name__ == "__main__":

    THREAD_NUM = int(sys.argv[1])       # Number of threads that will be created
    MAX_SOCKS = int(sys.argv[2])        # Max number of sockets at the same time

    sockQueue = Queue()

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
    print("Using " + str(THREAD_NUM) + " threads")
    print("and " + str(MAX_SOCKS) + " non-blocking sockets")
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

        for A in range(256):
            for B in range(256):

                # Check if range has already been scanned
                if scanning_util.rangeAlreadyScanned(scannedIps, f"{A}.{B}.0.0"):
                    continue

                rangeQueue.put((A, B))
    
        shuffle(rangeQueue.queue)       # Shuffling is more fun

        """
        Threads are build and started. The threads will check the sockets and try to get
        the Server List
        """

        for i in range(THREAD_NUM):
            t = Thread(target=checkSocketsThread, args=(outputFile, fileLock))
            t.daemon = True
            t.start()
    
        """
        The main thread will create the sockets and connect them to "random" ips, if they
        are succesfully connected, the connection will be checked by the threads
        """

        addSocketsToQueue(MAX_SOCKS, scannedIpsFile)
        
