from .base import Modifier as _BaseMod


class _Position(_BaseMod):
    category = "Position"
    mod_id = -1
    incap_message = "unimplemented"


class Dead(_Position):
    mod_id = 0
    incap_message = "Lie still; you are |rDEAD!|n"


class MortallyWounded(_Position):
    name = "Mortally Wounded"
    mod_id = 1
    incap_message = "You are in pretty bad shape, unable to do anything!"


class Incapacitated(_Position):
    mod_id = 2


class Stunned(_Position):
    mod_id = 3
    incap_message = "All you can do right now is think about the stars!"


class Sleeping(_Position):
    mod_id = 4
    incap_message = "In your dreams, or what?"


class Resting(_Position):
    mod_id = 5
    incap_message = "Nah... You feel too relaxed to do that..."


class Sitting(_Position):
    mod_id = 6
    incap_message = "Maybe you should get on your feet first?"


class Fighting(_Position):
    mod_id = 7
    incap_message = "No way! You're fighting for your life!"


class Standing(_Position):
    mod_id = 8
