class BitRecord:
    '''
    A class for representing a limited history of key presses.
    '''
    def __init__(self):
        self.bits = [0,0,0,0]
        self.frame = 0

    def Clear(self):
        for i in range(0,4):
            self.bits[i] = 0


