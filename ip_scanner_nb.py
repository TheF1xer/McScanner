import socket
from io import FileIO
import os
import sys
import time
from threading import Lock, Thread
from queue import Queue
from random import shuffle

from util import minecraft_util, scanning_util


rangeQueue: Queue = Queue()
sockQueue: Queue
SOCKET_TIMEOUT_SECS = 0.5


def scanSock(sock: socket.socket, outputFile: FileIO, fileLock: Lock) -> None:
    pass


def checkSocketsThread(outputFile: FileIO, fileLock: Lock) -> None:
    """
    I don't like the implementations but it is what it is
    """

    while True:
        if not sockQueue.empty():
            timedSock: scanning_util.TimedSocket = sockQueue.get()

            if timedSock.isConnected():
                scanSock(timedSock.sock, outputFile, fileLock)
                return

            if timedSock.getTimePassedSeconds() > SOCKET_TIMEOUT_SECS:
                return

            # If socket is not connected and it has not timedout, put it back in queue
            sockQueue.put(timedSock)


def addSocketsToQueue() -> None:
    """
    Creates sockets, tries to connect them to an ip and
    adds them to the queue
    """

    while not rangeQueue.empty():
        ipRange: tuple = rangeQueue.get()
        print(f"Scanning: {ipRange[0]}.{ipRange[1]}.0.0")

        for X in range(256):
            for Y in range(256):

                while not sockQueue.full():
                    ip = f"{ipRange[0]}.{ipRange[1]}.{X}.{Y}"
                    timedSock = scanning_util.TimedSocket(ip, minecraft_util.DEFAULT_PORT)
                    sockQueue.put(timedSock)


if __name__ == "__main__":

    THREAD_NUM = int(sys.argv[1])
    MAX_SOCKS = int(sys.argv[2])

    sockQueue = Queue(maxsize=MAX_SOCKS)

    # Save scan results to new file
    if not os.path.exists("scans"):
        os.mkdir("scans")

    fileName = f"scans/{time.strftime('%Y%m%d-%H%M%S')}.txt"


    print("-----------------------------------------------")
    print("TheF1xer's Minecraft Server Scanner")
    print("Saving results to file: " + fileName)
    print("")
    print("Using " + str(THREAD_NUM) + " threads")
    print("and " + str(MAX_SOCKS) + " non-blocking sockets")
    print("-----------------------------------------------")
    print("")

    with open(fileName, "w") as outputFile:
        fileLock = Lock()

        # Build range queue
        for A in range(256):
            for B in range(256):
                rangeQueue.put((A, B))
    
        shuffle(rangeQueue.queue)

        # Threads
        for i in range(THREAD_NUM):
            t = Thread(target=checkSocketsThread, args=(outputFile, fileLock))
            t.daemon = True
            t.start()
    
        # Main Thread
        addSocketsToQueue()
        
