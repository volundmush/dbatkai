from .base import Modifier as _BaseMod


class _RoomSector(_BaseMod):
    category = "SectorType"
    mod_id = -1
    map_key = "o"
    map_name = None

    @classmethod
    def get_map_name(cls):
        if cls.map_name:
            return cls.map_name
        return cls.get_name()


class Inside(_RoomSector):
    mod_id = 0
    map_key = "|xI|n"

    def is_providing_light(self, obj) -> bool:
        return True


class City(Inside):
    mod_id = 1
    map_key = "|wC|n"


class Field(_RoomSector):
    mod_id = 2
    map_key = "|gP|n"
    map_name = "Plain"


class Forest(_RoomSector):
    mod_id = 3
    map_key = "|GF|n"


class Hills(_RoomSector):
    mod_id = 4
    map_key = "|YH|n"


class Mountain(_RoomSector):
    mod_id = 5
    map_key = "|XM|n"


class WaterSwim(_RoomSector):
    mod_id = 6
    map_key = "|C~|n"
    map_name = "Shallow Water"


class WaterNoSwim(_RoomSector):
    mod_id = 7
    map_key = "|bW|n"
    map_name = "Water"


class Flying(_RoomSector):
    mod_id = 8
    map_key = "|cS|n"
    map_name = "Sky"


class Underwater(_RoomSector):
    mod_id = 9
    map_key = "|BU|n"


class Shop(_RoomSector):
    mod_id = 10
    map_key = "|M$|n"


class Important(_RoomSector):
    mod_id = 11
    map_key = "|m#|n"


class Desert(_RoomSector):
    mod_id = 12
    map_key = "|yD|n"


class Space(_RoomSector):
    mod_id = 13


class Lava(_RoomSector):
    mod_id = 14
    map_key = "|rL|n"
