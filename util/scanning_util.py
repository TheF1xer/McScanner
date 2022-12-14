import socket
import time
from io import TextIOWrapper
from threading import Lock


def writeServerToFileLock(ip: str, jsonObj: dict, file: TextIOWrapper, fileLock: Lock):
    fileLock.acquire()

    try:
        file.write(ip + " | " +  str(jsonObj["version"]["name"]) + " | " + str(jsonObj["players"]) + "\n")

        print("")
        print(ip)
        print(str(jsonObj["version"]["name"]))
        print(str(jsonObj["players"]))
        print("")

    except:
        pass

    fileLock.release()


def getScannedIps(file: TextIOWrapper) -> list:
    file.seek(0)
    return file.read().splitlines()


def rangeAlreadyScanned(scannedIps: list, ipRange: str) -> bool:
    return scannedIps.count(ipRange) > 0


class TimedSocket:
    sock: socket.socket
    ip: str
    port: int
    lastTime: float

    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.sock.connect_ex((ip, port))

        self.lastTime = time.time()


    def restartTimer(self) -> None:
        self.lastTime = time.time()


    def getTimePassedSeconds(self) -> float:
        return time.time() - self.lastTime


    def isConnected(self) -> bool:
        """
        Checks socket connection status
        Sadly, this is the only way I know of checking the connection :(
        """

        try:
            self.sock.send(b'')
            return True
        except:
            return False
