import random
import socket
import selectors


# Packet class, split of data
class Packet:
    maxDataLength = 500

    def __init__(self):
        self.Start = False
        self.End = False
        self.Index = 0
        self._maxIndex = 500;
        self._maxDataLength = 1000;
        self.data = ""
        self._Valid = False

        self._encoding = 'utf-8'

    def _getDataString(self):
        rString = ""
        rString += str(int(self.Start))
        rString += str(int(self.End))

        indexString = str(self.Index)
        if len(indexString) < len(str(self._maxIndex)):
            diff = len(str(self._maxIndex)) - len(indexString)
            plusString = ""

            for i in range(diff):
                plusString += "0"

            rString += plusString

        rString += indexString

        dataString = self.data
        if len(dataString) > self._maxDataLength:
            raise ValueError('Data is too large')

        while len(dataString) < self._maxDataLength:
            dataString += " "

        rString += dataString
        return rString

    # Send data string over a socket object
    def Send(self, socketObj=socket.socket, data="No Data"):
        self.data = data
        sendBytes = bytearray()
        sendBytes += bytes(self._getDataString(), self._encoding)
        socketObj.sendall(sendBytes)

    # Recieve a data string from a socket object
    def Recv(self, socketObj):
        bString = bytes(self._getDataString(), self._encoding)
        data = b''
        try:
            data = socketObj.recv(len(bString))
        except:
            self._Valid = False
            return False

        stringData = data.decode(self._encoding)

        if len(stringData) == 0:
            return False

        stringSplits = []
        stringSplits.append(stringData[0:1])
        stringSplits.append(stringData[1:2])
        stringSplits.append(stringData[2:5])
        stringSplits.append(stringData[5:])

        # Check if data has been recieved and if it's valid
        numbercheck = 0
        for i in range(3):
            numbercheck += stringSplits[i].isnumeric()
        if numbercheck == 3:
            self.Start = int(stringSplits[0])
            self.End = int(stringSplits[1])
            self.Index = int(stringSplits[2])
            self.data = stringSplits[3]
            self.data = self.data.strip()
            self._Valid = True

        return True

    def CheckContent(self):
        return self._Valid


# Function holder used by both host and clients
class Connection:
    def _SelectorReceive(socket, selector):
        """
        Recieve data group from the socket object if any is available.
        :param socket: Socket object to read from
        :param selector: Selector object tied to the socket
        :return: Returns data (if any available) from the scoket
        """
        inboundData = []
        readingLoop = True
        totalQuantity = 0
        currentQuantity = 0
        reading = False
        while readingLoop:
            # Wait for messsage
            events = selector.select(0.01);
            for key, mask in events:
                if mask & selectors.EVENT_READ:
                    readPacket = Packet()
                    readPacket.Recv(socket)
                    # Do noithing if not a valid packet
                    if readPacket.CheckContent():
                        # Got a starting packet. continue
                        if reading == False and readPacket.Start == True:
                            reading = True
                            totalQuantity = readPacket.Index

                        if reading:
                            currentQuantity += 1
                            inboundData.append(readPacket.data)

                            # This packet is last, stop reading
                            if readPacket.End == True:
                                readingLoop = False
                    # Empty packet received
                    # This can be a sign of a disconnection
                    else:
                        return
                else:
                    return

        if totalQuantity != currentQuantity:
            inboundData = []
        return inboundData

    def _SelectorSend(socket, selector, dataList):
        """
        :param socket: A socket object
        :param selector: The selector bind to the socket object
        :param dataList: List of strings to send over the socket
        :return: Returns false on error
        """
        noError = True
        # Loop through packets/data and send
        quantity = len(dataList)
        packet = 0
        for packet in range(quantity):
            # Wait until ready to send
            events = selector.select()
            for key, mask in events:
                # Ready to send
                if mask & selectors.EVENT_WRITE:
                    sendPacket = Packet()
                    if packet == 0:
                        sendPacket.Start = True
                        sendPacket.Index = quantity

                    if packet >= quantity - 1:
                        sendPacket.End = True
                    try:
                        sendPacket.Send(socket, str(dataList[packet]))
                    except:
                        noError = False

        return noError


# Reserved messages that are automatically handled/sent by client/host
class ReservedMessage:
    Ping = ["Ping"]
    Close = ["CloseConnection"]


class Host(Connection):
    def __init__(self, IP, Port, clientMax=10):
        """
        Create Host socket
        :param IP: The Host's IP Address
        :param Port: The Host's Port number
        :param clientMax: The max number of clients this host can have
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((IP, Port))
        self.socket.listen(clientMax)
        self.socket.setblocking(False)

        self.clients = []
        self.maxClients = clientMax
        self.Connections = []
        self.eventSelector = []
        self.clientLimit = clientMax
        for i in range(clientMax + 1):
            self.Connections.append((socket.socket, "", False))
            self.eventSelector.append(selectors.DefaultSelector())
        self.connectSelector = selectors.DefaultSelector()
        self.connectSelector.register(self.socket, selectors.EVENT_READ)

    def _acceptClient(self, clientSocket):
        """
        Private function to accept incoming clients to host
        :param clientSocket: Socket object of client
        :return: 
        """
        insertIndex = -1
        for i in range(self.maxClients):
            if not self.Connections[i][2]:
                insertIndex = i
                break

        Conn, Addr = clientSocket.accept()
        self.Connections[insertIndex] = (Conn, Addr, True)
        Conn.setblocking(False)
        self.eventSelector[insertIndex] = selectors.DefaultSelector()
        self.eventSelector[insertIndex].register(Conn, selectors.EVENT_READ | selectors.EVENT_WRITE)

        # Host is full send message to client to close
        if insertIndex == self.clientLimit:
            self.SendData(ReservedMessage.Close, self.clientLimit)
        # Report successful connection
        else:
            print(F"Connection Accepted from {Addr}")

        return insertIndex

    def ReceiveMessage(self, clientSlot):
        """
        Receive a message from a client
        :param clientSlot: Index slot of the client
        :return: The message received (if any available)
        """
        returnData = []
        connectEvent = self.connectSelector.select(0.001)
        for key, eventMask in connectEvent:
            if eventMask & selectors.EVENT_READ:
                self._acceptClient(key.fileobj)

        if self.Connections[clientSlot][2]:
            inData = Connection._SelectorReceive(
                self.Connections[clientSlot][0],
                self.eventSelector[clientSlot]
            )
            if inData:
                returnData = inData

        return returnData

    def SendData(self, dataList, clientSlot=0):
        """
        Send data to a specific client
        :param dataList: List of strings to send
        :param clientSlot: Index of the client to send to
        :return: None
        """
        # The connection is not active. Dont send anything
        if self.Connections[clientSlot][2] == False or type(dataList) != type([]):
            return

        if (
                Connection._SelectorSend(
                    self.Connections[clientSlot][0],
                    self.eventSelector[clientSlot],
                    dataList
                ) == False):
            self.CloseClient(clientSlot)

    def CloseClient(self, index):
        """
        Close a client off from host
        :param index: Client index to close
        :return: None
        """
        print(F"Closing connection with client: {self.Connections[index][1]}")
        self.Connections[index][0].shutdown(socket.SHUT_RDWR)
        self.Connections[index][0].close()
        self.Connections[index] = (socket.socket, "", False)
        self.eventSelector[index].close()

    def CheckClient(self, clientIndex):
        """
        Check if a client is still active
        :param clientIndex: Client's Index to check
        :return: True, if client is connected. otherwise false
        """

        # If this message sends with no exception, the client is still connected
        if self.Connections[clientIndex][2]:
            self.SendData(["Ping"], clientIndex)

        return self.Connections[clientIndex][2]

    def __del__(self):
        for clientIndex in range(self.clientLimit):
            self.SendData(ReservedMessage.Close, clientIndex)
            self.CloseClient(clientIndex)

        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()


class Client(Connection):
    def __init__(self, hostIP, hostPort):
        """
        Create object and connect to host object
        :param hostIP: IP address of host
        :param hostPort: Port of host
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.Connected = False

        # Try to connect to server
        try:
            self.socket.connect((hostIP, hostPort))
        except:
            print(F"Connection  to {hostIP},{hostPort} failed")

        print(F"Connection  to {hostIP},{hostPort} success.")
        self.Connected = True
        self.socket.setblocking(False)
        self.eventSelector = selectors.DefaultSelector()
        self.eventSelector.register(self.socket, selectors.EVENT_READ | selectors.EVENT_WRITE)

    def ReceiveMessage(self):
        """
        Receive a message from host (if any available)
        :return: Returns the received message. Empty if there's nothing to read
        """

        # Client not connected to host. Do nothing
        if not self.Connected:
            return

        inData = Connection._SelectorReceive(self.socket, self.eventSelector)
        if inData:
            if inData == ReservedMessage.Close:
                self.__del__()
                print("Server is full. Closing client socket")
            elif inData == ReservedMessage.Ping:
                self.SendData(ReservedMessage.Ping)
        return inData

    def SendData(self, dataList):
        """
        Send List of strings to host
        :param dataList: Strings to send
        :return: None
        """
        if self.Connected == False:
            return

        if (
                Connection._SelectorSend(
                    self.socket,
                    self.eventSelector,
                    dataList) == False
        ):
            # Couldn't send data. Connection is broken
            self.Connected = False

    def __del__(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self.Connected = False
