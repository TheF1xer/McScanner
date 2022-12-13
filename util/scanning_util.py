import socket
import time

class TimedSocket:
    sock: socket.socket
    startTime: float
    
    def __init__(self, ip: str, port: int) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.sock.connect_ex((ip, port))

        self.startTime = time.time()

    def getTimePassedSeconds(self) -> float:
        return time.time() - self.startTime

    def isConnected(self) -> bool:
        """
        Checks socket connection status
        Sadly, this is the only way I know of checking the connection :(
        """

        try:
            self.sock.recv(1)
            return True
        except:
            return False
