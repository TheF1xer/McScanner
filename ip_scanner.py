import socket
from util import minecraft_util
import random

def getServerInfo(sock: socket.socket, addr: str, port: int):
    sock.settimeout(0.6)        # We want to give the server a little more time once it has already connected
    jsonInfo = None
    buffer = b''

    try:

        # Ask for Server List
        minecraft_util.serverListPing(sock, addr, port)
        minecraft_util.statusRequest(sock)

        # Get bytes until we stop receiving
        while True:
            buffer += sock.recv(4096)

    except:
        pass

    # Decode if we got a response
    if buffer != b'':
        jsonInfo = minecraft_util.decodeStatusResponse(buffer)

    return jsonInfo


def scanIp(addr: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.3)

    try:

        # Connect to Server
        sock.connect((addr, minecraft_util.DEFAULT_PORT))
        print(f"{addr} open port")

        # Try to get Server Info
        svInfo = getServerInfo(sock, addr, minecraft_util.DEFAULT_PORT)

        if svInfo != None:
            print(addr + " | " + str(svInfo["version"]["name"]) + " | " + str(svInfo["players"]))
            print("")

    except:
        pass

    sock.close()


if __name__ == "__main__":
    randomRange1 = list(range(256))
    randomRange2 = list(range(256))

    random.shuffle(randomRange1)
    random.shuffle(randomRange2)

    scanIp("155.248.209.22")
    scanIp("mc.hypixel.net")
    scanIp("constantiam.net")

    for A in randomRange1:
        for B in randomRange2:
            for C in range(256):
                print(f"Start: {A}.{B}.{C}.0")

                for D in range(256):
                    addr = f"{A}.{B}.{C}.{D}"
                    scanIp(addr)

