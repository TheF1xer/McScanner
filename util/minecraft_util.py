import socket
import json

DEFAULT_PORT = 25565        # Default Port for Minecraft Server

SEGMENT_BITS = 0x7F         # 01111111
CONTINUE_BITS = 0x80        # 10000000


def serverListPing(sock: socket.socket, addr: str, port: int):

    """
    Minecraft Packet (no compression):
    Length + Packet ID + Data
    """

    packetID = b'\x00'                                          # Already converted to VarInt
    data = b''

    protocolVersion = toVarInt(-1)
    addrStr = toMcStr(addr)                                     # Convert to Minecraft String format
    portShort = port.to_bytes(2, byteorder="big")               # Convert Port to Short
    nextState = toVarInt(1)

    data += protocolVersion
    data += addrStr
    data += portShort
    data += nextState

    """ Packet build """

    msg = packetID + data                                       # ID + Data
    msg = toVarInt(len(msg)) + msg                              # Append length of message

    sock.send(msg)


def statusRequest(sock: socket.socket):
    req = b'\x00'
    req = toVarInt(len(req)) + req
    
    sock.send(req)


def decodeStatusResponse(response: bytes):
    statusResponse = McPacket(response)

    """ Length (VarInt read) """
    statusResponse.readVarInt()

    """ Packet ID (VarInt read) """
    statusResponse.readVarInt()
    
    """ Data (VarInt -> length, UTF-8 string -> Json) """
    mcString = statusResponse.readMcString()
    
    jsonResponse = json.loads(mcString)
    return jsonResponse


def toVarInt(num: int):

    """ https://wiki.vg/Protocol#VarInt_and_VarLong """

    ret = b''

    if num < 0:
        num = num & 0xFFFFFFFF                          # Make sure numbers are at max 4 bits long (for neg numbers especially)

    while True:
        temp = num & SEGMENT_BITS
        num = num >> 7                                  # Next chunk

        if num == 0:
            ret += temp.to_bytes(1, byteorder="big")    # First bit must be 0 if we are done
            break

        temp = temp | CONTINUE_BITS                     # Fist bit must be 1 if there are still bits left
        ret += temp.to_bytes(1, byteorder="big")

    return ret


def toMcStr(string: str):
    encString = string.encode("utf-8")
    ret = toVarInt(len(encString))
    ret += encString

    return ret


class McPacket:
    index = 0   # Byte that is currently being read


    def __init__(self, response: bytes):
        self.response = response


    def readVarInt(self) -> int:
        """
        Reads the next VarInt in the Status Response Packet
        NOTE: This does not work for negative numbers, it is what it is
        """

        varInt = 0

        for i in range(5):  # Max length of a VarInt is 5 bytes
            tempNum = self.response[self.index] & SEGMENT_BITS
            isLast = self.response[self.index] & CONTINUE_BITS == 0
    
            tempNum = tempNum << 7 * i
            varInt += tempNum

            self.index += 1

            if isLast:
                break

        return varInt


    def readMcString(self) -> str:
        """
        Reads the next String with the MC Packet Format
        """

        strLength = self.readVarInt()
        mcString = self.response[self.index : self.index + strLength + 1].decode("utf-8")
        self.index += strLength

        return mcString

