import pygame
import MyGame
import random

ServerPort = 4500

LevelSize = 400;
ScoreLimit = 10;

class ReservedMessage:
    PlayerSlot = ["PlayerSlot",0]
    StatusText = ["StatusText",""]

class Player(MyGame.GameObject):
    def __init__(self, x = 0, y  = 0,playerSlot = 0):
        self.networkName = "PlayerPong"
        self.height = 100;
        self.width = self.height/3;
        self.x = x
        self.y = y
        self.speed = 0.2
        self.playerSlot = playerSlot;

        self.moveUP = False
        self.moveDown = False

        self.collisionRect = pygame.Rect(
            self.x - (self.width / 2),
            self.y - (self.height / 2),
            self.width,
            self.height
        )

    def input_update(self, gameWindow):
        self.moveUP = False
        self.moveDown = False

        if (gameWindow.keyPressed[pygame.K_w]):
            self.moveUP = True
        elif (gameWindow.keyPressed[pygame.K_s]):
            self.moveDown = True

    def update(self, gameWindow):
        if self.moveUP == True:
            self.y -= self.speed * gameWindow.deltaTime
        elif self.moveDown == True:
            self.y += self.speed * gameWindow.deltaTime

        self.collisionRect = pygame.Rect(
            self.x - (self.width / 2),
            self.y - (self.height / 2),
            self.width,
            self.height
        )

        topY = self.y - self.height/2
        bottomY = self.y + self.height/2

        if topY < 0:
            self.y = 0 + self.height/2
        elif bottomY > LevelSize:
            self.y = LevelSize - self.height/2

    def paint(self, gameWindow):
        drawRect = pygame.Rect(self.x - (self.width/2),self.y - (self.height/2),self.width,self.height)

        pygame.draw.rect(
            gameWindow.getSurface(),pygame.Color(100,0,0),drawRect
        )

    def NetworkStateReset(self):
        self.moveUP = False
        self.moveDown = False

    def GetNetworkDataList(self):
        data = []
        #Object Name
        data.append(self.networkName)
        data.append(str(int(self.moveUP)))
        data.append(str(int(self.moveDown)))
        #PlayerSlot
        data.append(str(self.playerSlot))
        data.append(str(self.x))
        data.append(str(self.y))
        return data

    def NetworkRecv(self, dataList, host = True):
        """
        Updates object from data off the network
        :param dataList: List of data from network
        :return: Void
        """
        if (type(dataList) != type([])):
            return
        elif (len(dataList) != len(self.GetNetworkDataList())):
            return

        self.NetworkStateReset()
        self.moveUP = bool(int(dataList[1]))
        self.moveDown = bool(int(dataList[2]))

        try:
            self.playerSlot = int(dataList[3])
            if not host:
                self.x = float(dataList[4])
                self.y = float(dataList[5])
        except:
            print("F Message misssmatch")
            print(F"{dataList}")

class Ball(MyGame.GameObject):
    def __init__(self, x = LevelSize/2, y = LevelSize/2, size = 20, baseSpeed = 0.1):
        self.networkName = "Ball"
        self.x = x
        self.xDir = 0;

        self.y = y
        self.yDir = 1;

        self.size = size
        self.baseSpeed = baseSpeed
        self.xSpeed = self.baseSpeed;
        self.ySpeed = self.baseSpeed * random.random()

        self.collisionRect = pygame.Rect(
            self.x - self.size/2,
            self.y - self.size/2,
            self.size,
            self.size
        )
        self.reset()

        self.LeftPoints = 0;
        self.RightPoints = 0;

    def CollisionCheckPlayer(self,playerList = [Player()]):
        collisionRects = []
        for p in playerList:
            if self.collisionRect.colliderect(p.collisionRect):
                self.xSpeed += self.xSpeed * 0.08;

                if self.collisionRect.centerx > p.collisionRect.centerx:
                    self.xDir = 1
                else:
                    self.xDir = -1

                yCollideOffset = self.y - p.y
                yCollideOffset = yCollideOffset / (p.height/2)
                self.yDir =  self.yDir - (yCollideOffset * 5)

                yDirLimit = 3
                if self.yDir > yDirLimit:
                    self.yDir = yDirLimit
                elif self.yDir < -yDirLimit:
                    self.yDir = -yDirLimit

    def reset(self):
        self.x = LevelSize/2
        self.y = LevelSize/2

        self.xSpeed = self.baseSpeed
        self.ySpeed = self.baseSpeed * random.random()
        self.spawnIdle = 20

        self.xDir = 0
        self.yDir = 0


        while self.xDir == 0:
            self.xDir = random.randint(-1, 1)
        while self.yDir == 0:
            self.yDir = random.randint(-1, 1)

    def scoreReset(self):
        self.LeftPoints = 0
        self.RightPoints = 0
        
    def update(self, gameWindow):
        if self.spawnIdle > 0:
            self.spawnIdle -= gameWindow.deltaTime/100
            return

        self.x += (self.xSpeed * gameWindow.deltaTime) * self.xDir
        self.y += (self.ySpeed * gameWindow.deltaTime) * self.yDir

        if self.x + self.size/2 > LevelSize:
            self.LeftPoints += 1
            self.reset()
        elif self.x - self.size/2 < 0:
            self.RightPoints += 1
            self.reset()

        if self.y + self.size/2 > LevelSize:
            self.y = LevelSize - self.size/2
            self.yDir = -self.yDir
        elif self.y - self.size/2 < 0:
            self.y = 0 + self.size/2
            self.yDir = -self.yDir

        self.collisionRect = pygame.Rect(
            self.x - self.size / 2,
            self.y - self.size / 2,
            self.size,
            self.size
        )

    def paint(self,gameWindow):
        drawRect = pygame.Rect(
            self.x - self.size/2,
            self.y - self.size/2,
            self.size,
            self.size
        )

        pygame.draw.rect(
            gameWindow.getSurface(),pygame.Color(255,255,255),drawRect
        )


    def GetNetworkDataList(self):
        data = []
        data.append(self.networkName)
        data.append(str(self.x))
        data.append(str(self.y))
        data.append(str(self.LeftPoints))
        data.append(str(self.RightPoints))

        return data

    def NetworkRecv(self, dataList):
        if (len(dataList) != len(self.GetNetworkDataList())):
            return

        try:
            self.x = float(dataList[1])
            self.y = float(dataList[2])
            self.LeftPoints = int(dataList[3])
            self.RightPoints = int(dataList[4])
        except:
            pass

class MidDivider(MyGame.GameObject):
    def __init__(self, width = 10):
        self.width = width

    def paint(self,gameWindow):
        midX = LevelSize / 2
        midY = LevelSize / 2
        drawRect = pygame.Rect(
            midX - self.width / 2,
            midY - LevelSize / 2,
            self.width,
            LevelSize
        )

        pygame.draw.rect(
            gameWindow.getSurface(), pygame.Color(0, 0, 255), drawRect
        )
