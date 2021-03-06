'''Provide event queuing and transmission facilities.

This module provides a set of classes for implementing an asynchronous event
based system with events that can be transmitted over a network (or other
byte-oriented stream).'''

class Event:
    '''Base class for events processed with an EventQueue.'''
    
    def Serialize(self):
        '''Serialize this object into a tuple.
        
        This method should be overridden by the child class. It should represent
        the event object as a tuple consisting only of the following types:
        - int
        - float
        - str
        
        This representation should be returned by this method. The tuple retured
        by this method is converted to a bytes object by the eventqueue module.
        The reason for the restriction on types in the tuple is that these are
        the types understood by the eventqueue module.'''
        
        raise NotImplementedError
    
    @staticmethod
    def Deserialize(serialized_tuple):
        '''Construct an Event derrived object from a tuple that is returned from
        Serialize.
        
        This static method should be overridden by the child class. It should
        construct an Event object of the child class type using the serialized
        data int 'serialized_tuple'.
        
        Arguments:
        serialized_tuple -- The representation of the event object as returned
                            by Serialize.'''
        
        raise NotImplementedError
    
    @staticmethod
    def GetAssumedDeserializationTypes():
        '''Return the types that the first fields of serialized data for this
        event.
        
        Deserialization requires knowledge of the types to which the byte stream
        should be converted. This information can be included in the byte
        stream, but it's more efficient for it to be known by both sides without
        spending bytes describing it. This static method can be overridden by
        the subclass to provide this information. An event may be transmitted
        with fewer than are returned by this method without cost. An event may
        be transmitted with more fields, in which case the remaining fields will
        be described by the tuple to bytes serializer. It is an error for the
        first fields of a serialized event to fail to match the types returned
        by this method.
        
        This static method returns a tuple of (serializable) types.'''
        
        return ()

class EventTransmissionHandler:
    '''Allow EventQueue objects to transmit events over a network.
    
    The EventQueue class may be used to transfer events over a network. In
    this case, a EventTransmissionHandler object is required to provide an
    interface between the EventQueue and the network handling code.'''
    
    def WaitAndReceiveEventData(self):
        '''Wait for a serialized event, and return it.
        
        This method should be overridden by the child class. It should wait for
        an event to be received over the network, and return its data (as
        transmitted over the network) once received. This method may be called
        from a separate thread <or process if we get thread blocking issues>.
        Calling this method from a separate thread allows EventQueue objects to
        be used in a non-blocking manner when waiting for events to be received
        over the network.'''
        
        raise NotImplementedError
    
    def TransmitEventData(self, event_data):
        '''Transmit an event's serialized data over the network.
        
        This method should be overridden by the child class so that it can be
        called by an EventQueue object to transmit an event over the network.
        Like WaitAndReceiveEventData, this method may be called from a separate
        thread <or process>.
        
        Arguments:
        event_data -- The serialized event data to transmit over the network.'''
        
        raise NotImplementedError

class EventQueue:
    '''An event queue class is responsible for managing Event objects, and
    delivering them to their destination.'''
    
    def __init__(self):
        self._transmission_handler = None
        self._subscriptions = list()
    
    def PostEvent(self, event, transmit = True, subscription = False):
        '''Add an event to the event queue.
        
        This method adds an event to the event queue to be processed. Events are
        processed as follows:
        1) If transmit is true, the event is serialized and transmitted over the
           network. This raises an exception if no EventTransmissionHandler is
           registered to the EventQueue.
        2) If subscription is true, all event handlers subscribed to the event's
           type are called.
        
        Arguments:
        event        -- The event to be added to the queue.
        transmit     -- True if the event should be transmitted over the
                        network, and False otherwise.
        subscription -- True if the event should be handled by subscribers to
                        this event type, and False otherwise.'''
        
        # Send the event to its subscribers
        if subscription:
            for event_type,handler in self._subscriptions:
                if isinstance(event, event_type):
                    handler(event)
    
    def RegisterEventHandler(self, event_type, handler):
        '''Register an event handler.
        
        Event objects are transfered to their users via event handlers that are
        registered by this method. The event handler 'handler' is called with a
        single argument: the Event object to be handled. Objects that wish to
        subscribe to events should therefore do so with a lambda function that
        calls a method (including its 'self' parameter).'''
        
        self._subscriptions.append((event_type, handler))
    
    def RegisterEventTransmissionHandler(self, transmission_handler):
        '''Register an EventTransmissionHandler object to handle transmission of
        events over a network.
        
        If this method is called more than once, the transmission handler will
        be replaced. If this method is called with None, the transmission
        handler will be removed.
        
        Arguments:
        transmission_handler -- The transmission handler to use to send events
                                over the network from now on.'''
    
    def RegisterEventType(self, event_type):
        '''Register an event type.
        
        Event type registration is important, as events are assigned a unique
        integer to facilitate their transmission over the network. This method
        associates Event type 'event_type' with such an integer. It is important
        that all EventQueue objects handling the same Event types call this
        method with types in the same order so that the event types recieve the
        same number. It is not necessary to register events if there is no
        EventTransmissionHandler associated with this EventQueue.
        
        Arguments:
        t -- The type to register. Should be a subclass of Event.'''
