#Blueprint for a gameobject
class GameObject:
    x = 0;
    y = 0;
    def __init__(self):
        pass

    def update(self):
        pass

    def paint(self):
        pass

    #Get list summary of object for sending over network
    def GetNetworkDataList(self):
        pass

    def NetworkRecv(self, dataList):
        pass
