import pygame

class Window:
    def __init__(self, width = 300, height = 300, sizeable = False):
        if sizeable == True:
            sizeable = pygame.RESIZABLE
        else:
            sizeable = False
        self.display = pygame.display.set_mode((width, height), (pygame.HWSURFACE|sizeable))
        self.surface = pygame.display.get_surface()
        self.focus = False
        self.events = []
        self.mousePressed = []
        self.mouseDown = []
        self.mousePos = ()
        self.keyPressed = []
        self.keyDown = []
        self.clock = pygame.time.Clock()
        self.deltaTime = 0;
        self.fps = 0;

    #Set the window title
    def setTitle(self,name):
        pygame.display.set_caption(name)

    #Get events,deltaTime and keyinput
    def update(self, framerate = 60):
        self.clock.tick(framerate)

        self.focus = pygame.key.get_focused() and pygame.mouse.get_focused()
        self.events = pygame.event.get()
        self.fps = self.clock.get_fps()
        self.deltaTime = self.clock.get_time()

        self.keyDown = []
        self.mouseDown = []
        self.keyPressed = pygame.key.get_pressed()
        self.mousePressed = pygame.mouse.get_pressed()
        for e in self.events:
            if e.type == pygame.KEYDOWN:
                self.keyDown.append(e.key)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                self.mouseDown = pygame.mouse.get_pressed()

    def flip(self):
        pygame.display.flip()

    #Get the window surface
    def getSurface(self):
        return pygame.display.get_surface()

    #Close pygame
    def __del__(self):
        pygame.quit()


