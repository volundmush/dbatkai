from advent.handlers import EquipmentHandler, InventoryHandler, WeightHandler
from evennia.utils.utils import lazy_property


class GameObj:

    @lazy_property
    def inventory(self):
        return InventoryHandler(self)


    @lazy_property
    def equipment(self):
        return EquipmentHandler(self)


    @lazy_property
    def weight(self):
        return WeightHandler(self)