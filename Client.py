import selectors
import socket
import MyNetwork
import pygame
import PyWindow
import Pong.MyPong

pygame.init()

HOSTIP = '127.0.0.1'
PORT = Pong.MyPong.ServerPort

MainClient = MyNetwork.Client(HOSTIP, PORT)

MainWindow = PyWindow.Window(Pong.MyPong.LevelSize, Pong.MyPong.LevelSize)

ClientPlayer = Pong.MyPong.Player()

Players = [
    Pong.MyPong.Player(
        0,
        Pong.MyPong.LevelSize / 2,
        0
    ),
    Pong.MyPong.Player(
        Pong.MyPong.LevelSize,
        Pong.MyPong.LevelSize / 2,
        1
    )
]

GameBall = Pong.MyPong.Ball()
MidDivide = Pong.MyPong.MidDivider()
TextFont = pygame.font.Font("Arial Font\\arial.ttf", 50)
PlayerSlot = -1
StatusText = ""

appLoop = True
# Dont start app loop if couldnt connect
if MainClient.Connected == False:
    appLoop = False

while appLoop:
    MainWindow.update(60)

    for event in MainWindow.events:
        if event.type == pygame.QUIT:
            appLoop = False

    inboundData = []
    while True:
        data = MainClient.ReceiveMessage()
        if data:
            inboundData.append(data)
        else:
            break

    for message in inboundData:
        # Player slot given
        if message[0] == Pong.MyPong.ReservedMessage.PlayerSlot[0]:
            PlayerSlot = int(message[1])

        # Update player object
        elif message[0] == Players[0].networkName:
            slot = int(message[3])
            Players[slot].NetworkRecv(message, False)
        # Update Gameball
        elif message[0] == GameBall.networkName:
            GameBall.NetworkRecv(message)
        # Update Status text
        elif message[0] == Pong.MyPong.ReservedMessage.StatusText[0]:
            StatusText = message[1]

    # Player is connected, update objects from network
    if PlayerSlot >= 0:
        Players[PlayerSlot].input_update(MainWindow)
        playerData = Players[PlayerSlot].GetNetworkDataList()
        MainClient.SendData(playerData)

    WindowName = "Multi Pong Client"
    if PlayerSlot > -1:
        WindowName += ": Player" + str(PlayerSlot + 1)
    MainWindow.setTitle(WindowName)

    # Paint The Scene
    MainWindow.getSurface().fill(
        pygame.Color(0, 0, 0)
    )
    MidDivide.paint(MainWindow)

    StateTextSurface = TextFont.render(
        StatusText, 0,
        pygame.Color(0, 200, 0)
    )

    TextWidth = StateTextSurface.get_width()
    TextHeight = StateTextSurface.get_height()

    MainWindow.getSurface().blit(
        StateTextSurface,
        (
            Pong.MyPong.LevelSize / 2 - TextWidth / 2,
            Pong.MyPong.LevelSize / 2 - TextHeight / 2
        )
    )

    for p in Players:
        p.paint(MainWindow)
    GameBall.paint(MainWindow)

    MainWindow.flip()
