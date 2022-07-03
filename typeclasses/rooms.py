"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import DefaultRoom
from evennia.utils.utils import lazy_property
from advent.handlers import FlagsHandler, FlagHandler
from .mixins import GameObj


class Room(DefaultRoom, GameObj):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """

    @lazy_property
    def room_flags(self):
        return FlagsHandler(self, "room_flags", "RoomFlags")

    @lazy_property
    def sector_type(self):
        return FlagHandler(self, "sector_type", "SectorType")
