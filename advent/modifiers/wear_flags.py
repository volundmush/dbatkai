from .base import Modifier as _BaseMod


class _WearFlag(_BaseMod):
    category = "WearFlags"
    modifier_id = -1



class Take(_WearFlag):
    modifier_id = 0


class Finger(_WearFlag):
    modifier_id = 1


class Neck(_WearFlag):
    modifier_id = 2


class Body(_WearFlag):
    modifier_id = 3


class Head(_WearFlag):
    modifier_id = 4


class Legs(_WearFlag):
    modifier_id = 5


class Feet(_WearFlag):
    modifier_id = 6


class Hands(_WearFlag):
    modifier_id = 7


class Arms(_WearFlag):
    modifier_id = 8


class Shield(_WearFlag):
    modifier_id = 9


class About(_WearFlag):
    modifier_id = 10


class Waist(_WearFlag):
    modifier_id = 11


class Wrist(_WearFlag):
    modifier_id = 12


class Wield(_WearFlag):
    modifier_id = 13


class Hold(_WearFlag):
    modifier_id = 14


class Pack(_WearFlag):
    modifier_id = 15


class Ear(_WearFlag):
    modifier_id = 16


class Wings(_WearFlag):
    modifier_id = 17


class Eye(_WearFlag):
    modifier_id = 18