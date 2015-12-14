class MockEventSocket:
    '''A class for simulating socket errors.
    This class is intended to be used in tests.
    '''
    sock = None
    def ReadEvent(self):
        raise Exception

    def UnreadEvent(self):
        pass

    def WriteEvent(self, evt):
        raise Exception

    def Close(self):
        pass

    def GetPeerName(self):
        return ''
