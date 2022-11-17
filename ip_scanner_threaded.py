import socket
import sys
import threading
import time
import os
from io import TextIOWrapper
from threading import Lock, Thread
from random import shuffle
from queue import Queue
import util

rangeQueue = Queue()

def writeServerToFile(ip: str, jsonObj, file: TextIOWrapper, fileLock: Lock):
    fileLock.acquire()
    file.write(ip + " | " + str(jsonObj["version"]["name"]) + " | " + str(jsonObj["players"]) + "\n")
    fileLock.release()

def getServerInfo(sock: socket.socket, addr: str, port: int):
    sock.settimeout(0.6)        # We want to give the server a little more time once it has already connected
    jsonInfo = None
    buffer = b''

    try:

        # Ask for Server List
        util.serverListPing(sock, addr, port)
        util.statusRequest(sock)

        # Get bytes until we stop receiving
        while True:
            buffer += sock.recv(4096)

    except:
        pass

    # Decode if we got a response
    if buffer != b'':
        jsonInfo = util.decodeStatusResponse(buffer)

    return jsonInfo


def scanIp(ip: str, file: TextIOWrapper, fileLock: Lock) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.3)

    try:

        # Connect to Server
        sock.connect((ip, util.DEFAULT_PORT))

        # Try to get Server Info
        svInfo = getServerInfo(sock, ip, util.DEFAULT_PORT)

        if svInfo != None:
            writeServerToFile(ip, svInfo, file, fileLock)

            print("")
            print(ip + " | " + str(svInfo["version"]["name"]) + " | " + str(svInfo["players"]))
            print("")

    except:
        pass

    sock.close()


def scanIpRange(file: TextIOWrapper, fileLock: Lock) -> None:
    while not rangeQueue.empty():
        ipRange = rangeQueue.get()

        for X in range(256):
            print(f"Start: {ipRange[0]}.{ipRange[1]}.{X}.0")

            for Y in range(256):
                ip = f"{ipRange[0]}.{ipRange[1]}.{X}.{Y}"
                scanIp(ip, file, fileLock)


if __name__ == "__main__":

    THREAD_NUM = int(sys.argv[1])

    # Scans for servers and save them
    if not os.path.exists("scans"):
        os.mkdir("scans")

    fileName = f"scans/{time.strftime('%Y%m%d-%H%M%S')}.txt"
    print(fileName)

    with open(fileName, "w") as outputFile:
        fileLock = threading.Lock()

        # Build queue
        for A in range(256):
            for B in range(256):
                rangeQueue.put((A, B))
    
        shuffle(rangeQueue.queue)

        # Threads
        for i in range(THREAD_NUM):
            t = Thread(target=scanIpRange, args=(outputFile, fileLock))
            t.daemon = True
            t.start()
    
        # Main Thread
        scanIpRange(outputFile, fileLock)
