class BitRecord:
    '''
    A class for representing a limited history of key presses.
    bits[0] -- Player 1.
    bits[1] -- Player 2.
    bits[2] -- Player 3.
    bits[3] -- Apply PlayFromStateWithPlayer().
    bits[4] -- Score flag.
    '''
    def __init__(self):
        self.bits = [0,0,0,0,0]
        self.frame = 0

    def Clear(self):
        for i in range(0,5):
            self.bits[i] = 0


