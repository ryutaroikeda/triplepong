import os
import sys
import unittest

sys.path.append(os.path.abspath('src'))
import eventqueue

class Event(eventqueue.Event):
    def __init__(self, item):
        self.item = item
class EventA(Event):
    pass
class EventB(Event):
    pass
class EventC(Event):
    pass
class EventD(Event):
    pass

class EventQueueTest(unittest.TestCase):
    def _event_handler(self, name, event):
        self._event_handler_test[name].append(event.item)
    
    def test_local_event_subscriptions(self):
        # Set up the event handler dictionary
        self._event_handler_test = dict()
        self._event_handler_test['a'] = list()
        self._event_handler_test['b'] = list()
        self._event_handler_test['c'] = list()
        
        # Create the queue
        q = eventqueue.EventQueue()
        
        # Register some event types
        q.RegisterEventHandler(EventA, lambda e: self._event_handler('a', e))
        q.RegisterEventHandler(EventB, lambda e: self._event_handler('b', e))
        
        # Register an event type that we never use
        q.RegisterEventHandler(EventC, lambda e: self._event_handler('c', e))
        
        # Register a second B (to show behaviour in this case)
        q.RegisterEventHandler(EventB, lambda e: self._event_handler('b', e))
        
        # Post some normal local events
        q.PostEvent(EventB(3), False, True)
        q.PostEvent(EventA(1), False, True)
        q.PostEvent(EventA(2), False, True)
        q.PostEvent(EventB(4), False, True)
        
        # Post an event that the queue has no subscribers for
        q.PostEvent(EventD(5), False, True)
        
        # Post an event that is not intended for local distribution
        q.PostEvent(EventA(6), False, False)
        
        assert (
            self._event_handler_test == {
                'a': [1, 2],
                'b': [3, 3, 4, 4], # Remember, B subscribed twice
                'c': []
            }
        )

if __name__ == '__main__':
    unittest.main()