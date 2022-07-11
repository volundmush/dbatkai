from enum import IntEnum


class Size(IntEnum):
    UNDEFINED = -1
    FINE = 0
    DIMINUTIVE = 1
    TINY = 2
    SMALL = 3
    MEDIUM = 4
    LARGE = 5
    HUGE = 6
    GARGANTUAN = 7
    COLOSSAL = 8


class Sex(IntEnum):
    NEUTER = 0
    MALE = 1
    FEMALE = 2


class Position(IntEnum):
    DEAD = 0
    MORTALLY_WOUNDED = 1
    INCAPACITATED = 2
    STUNNED = 3
    SLEEPING = 4
    RESTING = 5
    SITTING = 6
    FIGHTING = 7
    STANDING = 8
