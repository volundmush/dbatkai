from .objects import Object
from evennia.utils.utils import lazy_property
from advent.handlers.basic import FlagsHandler, FlagHandler
from .mixins import GameObj
from evennia.utils.ansi import ANSIString


class Item(GameObj, Object):

    @lazy_property
    def item_flags(self):
        return FlagsHandler(self, "item_flags", "ItemFlags")

    @lazy_property
    def affect_flags(self):
        return FlagsHandler(self, "affect_flags", "AffectFlags")

    @lazy_property
    def item_type(self):
        return FlagHandler(self, "item_type", "ItemType")

    def get_vnum_display(self):
        if self.db.item_vnum:
            return f"|g[I-{self.db.item_vnum}]|n"
        return None
