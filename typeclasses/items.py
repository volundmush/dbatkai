from .objects import Object
from evennia.utils.utils import lazy_property
from advent.handlers import FlagsHandler
from .mixins import GameObj


class Item(Object, GameObj):

    @lazy_property
    def item_flags(self):
        return FlagsHandler(self, "item_flags", "ItemFlags")

    @lazy_property
    def affect_flags(self):
        return FlagsHandler(self, "affect_flags", "AffectFlags")
