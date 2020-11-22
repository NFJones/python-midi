import math

class EventRegistry:
    Events = {}
    MetaEvents = {}

    def register_event(cls, event, bases):
        if (Event in bases) or (NoteEvent in bases):
            assert event.statusmsg not in cls.Events, \
                            "Event %s already registered" % event.name
            cls.Events[event.statusmsg] = event
        elif (MetaEvent in bases) or (MetaEventWithText in bases):
            if event.metacommand is not None:
                assert event.metacommand not in cls.MetaEvents, \
                                "Event %s already registered" % event.name
                cls.MetaEvents[event.metacommand] = event
        else:
            raise ValueError("Unknown bases class in event type: "+event.name)
    register_event = classmethod(register_event)


class EventMetaClass(type):
    def __init__(cls, name, bases, dict):
        if name not in ['AbstractEvent', 'Event', 'MetaEvent', 'NoteEvent',
                        'MetaEventWithText']:
            EventRegistry.register_event(cls, bases)


class AbstractEvent(metaclass=EventMetaClass):
    name = "Generic MIDI Event"
    length = 0
    statusmsg = 0x0

    def __init__(self, **kw):
        if type(self.length) == int:
            defdata = [0] * self.length
        else:
            defdata = []
        self.tick = 0
        self.data = defdata
        for key in kw:
            setter_name = "set_{}".format(key)
            if hasattr(self, setter_name):
                setter = getattr(self, setter_name)
                setter(kw[key])
            setattr(self, key, kw[key])

    def __cmp__(self, other):
        if self.tick < other.tick: return -1
        elif self.tick > other.tick: return 1
        return cmp(self.data, other.data)

    def __baserepr__(self, keys=[]):
        keys = ['tick'] + keys + ['data']
        body = []
        for key in keys:
            val = getattr(self, key)
            keyval = "%s=%r" % (key, val)
            body.append(keyval)
        body = str.join(', ', body)
        return "midi.%s(%s)" % (self.__class__.__name__, body)

    def __repr__(self):
        return self.__baserepr__()


class Event(AbstractEvent):
    name = 'Event'

    def __init__(self, **kw):
        if 'channel' not in kw:
            kw = kw.copy()
            kw['channel'] = 0
        super(Event, self).__init__(**kw)

    def copy(self, **kw):
        _kw = {'channel': self.channel, 'tick': self.tick, 'data': self.data}
        _kw.update(kw)
        return self.__class__(**_kw)

    def __cmp__(self, other):
        if self.tick < other.tick: return -1
        elif self.tick > other.tick: return 1
        return 0

    def __repr__(self):
        return self.__baserepr__(['channel'])

    def is_event(cls, statusmsg):
        return (cls.statusmsg == (statusmsg & 0xF0))
    is_event = classmethod(is_event)


"""
MetaEvent is a special subclass of Event that is not meant to
be used as a concrete class.  It defines a subset of Events known
as the Meta events.
"""

class MetaEvent(AbstractEvent):
    statusmsg = 0xFF
    metacommand = 0x0
    name = 'Meta Event'

    def is_event(cls, statusmsg):
        return (statusmsg == 0xFF)
    is_event = classmethod(is_event)


"""
NoteEvent is a special subclass of Event that is not meant to
be used as a concrete class.  It defines the generalities of NoteOn
and NoteOff events.
"""

class NoteEvent(Event):
    length = 2

    def get_pitch(self):
        return self.data[0]
    def set_pitch(self, val):
        self.data[0] = val

    def get_velocity(self):
        return self.data[1]
    def set_velocity(self, val):
        self.data[1] = val

class NoteOnEvent(NoteEvent):
    statusmsg = 0x90
    name = 'Note On'

class NoteOffEvent(NoteEvent):
    statusmsg = 0x80
    name = 'Note Off'

class AfterTouchEvent(Event):
    statusmsg = 0xA0
    length = 2
    name = 'After Touch'

class ControlChangeEvent(Event):
    statusmsg = 0xB0
    length = 2
    name = 'Control Change'

    def set_control(self, val):
        self.data[0] = val
    def get_control(self):
        return self.data[0]

    def set_value(self, val):
        self.data[1] = val
    def get_value(self):
        return self.data[1]

class ProgramChangeEvent(Event):
    statusmsg = 0xC0
    length = 1
    name = 'Program Change'

    def set_value(self, val):
        self.data[0] = val
    def get_value(self):
        return self.data[0]

class ChannelAfterTouchEvent(Event):
    statusmsg = 0xD0
    length = 1
    name = 'Channel After Touch'

    def set_value(self, val):
        self.data[1] = val
    def get_value(self):
        return self.data[1]

class PitchWheelEvent(Event):
    statusmsg = 0xE0
    length = 2
    name = 'Pitch Wheel'

    def get_pitch(self):
        return ((self.data[1] << 7) | self.data[0]) - 0x2000
    def set_pitch(self, pitch):
        value = pitch + 0x2000
        self.data[0] = value & 0x7F
        self.data[1] = (value >> 7) & 0x7F

class SysexEvent(Event):
    statusmsg = 0xF0
    name = 'SysEx'
    length = 'varlen'

    def is_event(cls, statusmsg):
        return (cls.statusmsg == statusmsg)
    is_event = classmethod(is_event)

class SequenceNumberMetaEvent(MetaEvent):
    name = 'Sequence Number'
    metacommand = 0x00
    length = 2

class MetaEventWithText(MetaEvent):
    def __init__(self, **kw):
        super(MetaEventWithText, self).__init__(**kw)
        if 'text' not in kw:
            self.text = ''.join(chr(datum) for datum in self.data)
    
    def __repr__(self):
        return self.__baserepr__(['text'])

class TextMetaEvent(MetaEventWithText):
    name = 'Text'
    metacommand = 0x01
    length = 'varlen'

class CopyrightMetaEvent(MetaEventWithText):
    name = 'Copyright Notice'
    metacommand = 0x02
    length = 'varlen'

class TrackNameEvent(MetaEventWithText):
    name = 'Track Name'
    metacommand = 0x03
    length = 'varlen'

class InstrumentNameEvent(MetaEventWithText):
    name = 'Instrument Name'
    metacommand = 0x04
    length = 'varlen'

class LyricsEvent(MetaEventWithText):
    name = 'Lyrics'
    metacommand = 0x05
    length = 'varlen'

class MarkerEvent(MetaEventWithText):
    name = 'Marker'
    metacommand = 0x06
    length = 'varlen'

class CuePointEvent(MetaEventWithText):
    name = 'Cue Point'
    metacommand = 0x07
    length = 'varlen'

class ProgramNameEvent(MetaEventWithText):
    name = 'Program Name'
    metacommand = 0x08
    length = 'varlen'

class UnknownMetaEvent(MetaEvent):
    name = 'Unknown'
    # This class variable must be overriden by code calling the constructor,
    # which sets a local variable of the same name to shadow the class variable.
    metacommand = None

    def __init__(self, **kw):
        super(MetaEvent, self).__init__(**kw)
        self.metacommand = kw['metacommand']

    def copy(self, **kw):
        kw['metacommand'] = self.metacommand
        return super(UnknownMetaEvent, self).copy(kw)

class ChannelPrefixEvent(MetaEvent):
    name = 'Channel Prefix'
    metacommand = 0x20
    length = 1

class PortEvent(MetaEvent):
    name = 'MIDI Port/Cable'
    metacommand = 0x21

class TrackLoopEvent(MetaEvent):
    name = 'Track Loop'
    metacommand = 0x2E

class EndOfTrackEvent(MetaEvent):
    name = 'End of Track'
    metacommand = 0x2F

class SetTempoEvent(MetaEvent):
    name = 'Set Tempo'
    metacommand = 0x51
    length = 3

    def set_bpm(self, bpm):
        self.mpqn = int(float(6e7) / bpm)
    def get_bpm(self):
        return float(6e7) / self.mpqn

class SmpteOffsetEvent(MetaEvent):
    name = 'SMPTE Offset'
    metacommand = 0x54

class TimeSignatureEvent(MetaEvent):
    name = 'Time Signature'
    metacommand = 0x58
    length = 4

    def get_numerator(self):
        return self.data[0]
    def set_numerator(self, val):
        self.data[0] = val

    def get_denominator(self):
        return 2 ** self.data[1]
    def set_denominator(self, val):
        self.data[1] = int(math.log(val, 2))

    def get_metronome(self):
        return self.data[2]
    def set_metronome(self, val):
        self.data[2] = val

    def get_thirtyseconds(self):
        return self.data[3]
    def set_thirtyseconds(self, val):
        self.data[3] = val

class KeySignatureEvent(MetaEvent):
    name = 'Key Signature'
    metacommand = 0x59
    length = 2

    def get_alternatives(self):
        d = self.data[0]
        return d - 256 if d > 127 else d
    def set_alternatives(self, val):
        self.data[0] = 256 + val if val < 0 else val

    def get_minor(self):
        return self.data[1]
    def set_minor(self, val):
        self.data[1] = val

class SequencerSpecificEvent(MetaEvent):
    name = 'Sequencer Specific'
    metacommand = 0x7F
