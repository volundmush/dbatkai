"""
Room

Rooms are simple containers that has no location of their own.

"""

from athanor.typeclasses.rooms import AthanorRoom

from .objects import ObjectParent


class Room(ObjectParent, AthanorRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """

    def all_aspect_slots(self) -> dict[str, dict]:
        slots = super().all_aspect_slots()
        slots["sector_type"] = {}
        return slots