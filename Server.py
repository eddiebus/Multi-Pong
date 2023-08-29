import pygame
import MyNetwork
import PyWindow
import Pong.MyPong

pygame.init()

HOSTIP = '127.0.0.1'
PORT = Pong.MyPong.ServerPort

# Start the host
MainConnection = MyNetwork.Host(HOSTIP, PORT, 2)

# Create the window
MainWindow = PyWindow.Window(400, 400)
MainWindow.setTitle("Multi-Pong Server")

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
TextFont = pygame.font.Font("arial.ttf", 50)
StatusText = ""
ScoreLimit = 5

WinPlayer = -1


# 3 States for the game
class GameState:
    Waiting = "Waiting"
    Playing = "Playing"
    GameEnd = "GameEnd"

    stateTime = -1


ServerState = GameState.Waiting

AppLoop = True
while AppLoop == True:
    # Update Window Events
    MainWindow.update()
    for event in MainWindow.events:
        if event.type == pygame.QUIT:
            AppLoop = False

    inboundData = []
    for client in range(2):
        readLoop = True
        inboundData.append([])
        # Read loop for a client
        while readLoop:
            clientMessage = MainConnection.ReceiveMessage(client)
            if clientMessage:
                inboundData[client].append(clientMessage)
            else:
                readLoop = False

    GameState.stateTime += MainWindow.deltaTime / 200
    if ServerState == GameState.Waiting:
        StatusText = "Waiting..."
        if MainConnection.CheckClient(0) and MainConnection.CheckClient(1):
            ServerState = GameState.Playing
            GameState.stateTime = 0
    elif ServerState == GameState.Playing:

        if not MainConnection.CheckClient(0) or not MainConnection.CheckClient(1):
            ServerState = GameState.Waiting
            GameState.stateTime = 0
            GameBall.scoreReset()
            GameBall.reset()

        # Tell each client of their player slot
        for playerI in range(2):
            Message = Pong.MyPong.ReservedMessage.PlayerSlot
            Message[1] = str(playerI)
            MainConnection.SendData(Message, playerI)

            # Receive info on players
            for playerI in range(2):
                for message in inboundData[playerI]:
                    if message[0] == Players[playerI].networkName:
                        Players[playerI].NetworkRecv(message)
                        Players[playerI].update(MainWindow)

        GameBall.update(MainWindow)
        GameBall.CollisionCheckPlayer(Players)

        StatusText = str(GameBall.LeftPoints) + " | " + str(GameBall.RightPoints)

        # Send Info to clients
        for client in range(2):
            for p in Players:
                data = p.GetNetworkDataList()
                MainConnection.SendData(data, client)

            balldata = GameBall.GetNetworkDataList()
            MainConnection.SendData(balldata, client)

        # Check for winner
        if GameBall.LeftPoints == ScoreLimit:
            WinPlayer = 1
        elif GameBall.RightPoints == ScoreLimit:
            WinPlayer = 2

        # Player is decided, switch scene
        if WinPlayer > 0:
            GameBall.reset()
            ServerState = GameState.GameEnd
            GameState.stateTime = 0
    elif ServerState == GameState.GameEnd:
        StatusText = F"P{WinPlayer} Wins!"

        if GameState.stateTime > 30:
            GameBall.scoreReset()
            ServerState = GameState.Playing
            GameState.stateTimse = 0
            WinPlayer = -1

    # Send Status Text
    for client in range(2):
        statusData = Pong.MyPong.ReservedMessage.StatusText
        statusData[1] = StatusText
        MainConnection.SendData(statusData, client)

    # Render Objects
    MainWindow.getSurface().fill(pygame.Color(0, 0, 0))

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

    GameBall.paint(MainWindow)
    for p in Players:
        p.paint(MainWindow)

    MainWindow.flip()

pygame.quit()
