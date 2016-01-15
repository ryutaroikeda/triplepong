class BitRecord:
    '''
    A class for representing a history of key presses.
    Each element in bits is a size-bit integer. An event at frame f is 
    represented by a 1 on the (f mod size)-th bit. A reference frame self.frame
    is kept to avoid ambiguity. The bits represent the following events:
    bits[0] -- A key press for player 1.
    bits[1] -- A key press for player 2.
    bits[2] -- A key press for player 3.
    bits[3] -- Client use only. The record for p in PlayFromStateWithPlayer() 
                should be ignored, where p is the client.
    bits[4] -- A point was scored. This is used to count the score correctly.
    '''
    def __init__(self):
        self.bits = [0,0,0,0,0]
        self.frame = 0

    def Clear(self):
        for i in range(0,5):
            self.bits[i] = 0


