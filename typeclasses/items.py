from athanor.typeclasses.items import AthanorItem
from evennia.utils.utils import lazy_property
from athanor.modifiers import FlagsHandler, FlagHandler
from .mixins import GameObj
from evennia.utils.ansi import ANSIString
from advent.handlers import StatHandler
from evennia.contrib.rpg.rpsystem import ContribRPObject


class Item(GameObj, AthanorItem):

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

    @lazy_property
    def price(self):
        return StatHandler(self, "price", default=0)

    @lazy_property
    def price_per_day(self):
        return StatHandler(self, "price_per_day", default=0)