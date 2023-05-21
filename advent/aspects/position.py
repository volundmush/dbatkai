from .base import AdventAspect as _AdventAspect


class _Position(_AdventAspect):
    slot_type = "position"
    position_value = -1
    incap_message = "unimplemented"

    def __int__(self):
        return self.position_value


class Dead(_Position):
    position_value = 0
    incap_message = "Lie still; you are |rDEAD!|n"


class MortallyWounded(_Position):
    name = "Mortally Wounded"
    position_value = 1
    incap_message = "You are in pretty bad shape, unable to do anything!"


class Incapacitated(_Position):
    position_value = 2
    incap_message = "You are incapacitated and unable to do anything!"


class Stunned(_Position):
    position_value = 3
    incap_message = "All you can do right now is think about the stars!"


class Sleeping(_Position):
    position_value = 4
    incap_message = "In your dreams, or what?"


class Resting(_Position):
    position_value = 5
    incap_message = "Nah... You feel too relaxed to do that..."


class Sitting(_Position):
    position_value = 6
    incap_message = "Maybe you should get on your feet first?"


class Fighting(_Position):
    position_value = 7
    incap_message = "No way! You're fighting for your life!"


class Standing(_Position):
    position_value = 8
