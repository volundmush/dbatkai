from enum import IntEnum


class ExitDir(IntEnum):
    UNKNOWN = -1
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    UP = 4
    DOWN = 5
    NORTHWEST = 6
    NORTHEAST = 7
    SOUTHEAST = 8
    SOUTHWEST = 9
    INSIDE = 10
    OUTSIDE = 11

    def reverse(self) -> "ExitDir":
        match self:
            case ExitDir.NORTH:
                return ExitDir.SOUTH
            case ExitDir.EAST:
                return ExitDir.WEST
            case ExitDir.SOUTH:
                return ExitDir.NORTH
            case ExitDir.WEST:
                return ExitDir.EAST
            case ExitDir.UP:
                return ExitDir.DOWN
            case ExitDir.DOWN:
                return ExitDir.UP
            case ExitDir.NORTHWEST:
                return ExitDir.SOUTHEAST
            case ExitDir.NORTHEAST:
                return ExitDir.SOUTHWEST
            case ExitDir.SOUTHEAST:
                return ExitDir.NORTHWEST
            case ExitDir.SOUTHWEST:
                return ExitDir.NORTHEAST
            case ExitDir.INSIDE:
                return ExitDir.OUTSIDE
            case ExitDir.OUTSIDE:
                return ExitDir.INSIDE
            case _:
                return ExitDir.UNKNOWN

    def abbr(self) -> str:
        match self:
            case ExitDir.NORTH:
                return "N"
            case ExitDir.EAST:
                return "W"
            case ExitDir.SOUTH:
                return "S"
            case ExitDir.WEST:
                return "W"
            case ExitDir.UP:
                return "U"
            case ExitDir.DOWN:
                return "D"
            case ExitDir.NORTHWEST:
                return "NW"
            case ExitDir.NORTHEAST:
                return "NE"
            case ExitDir.SOUTHEAST:
                return "SE"
            case ExitDir.SOUTHWEST:
                return "SW"
            case ExitDir.INSIDE:
                return "I"
            case ExitDir.OUTSIDE:
                return "O"
            case _:
                return "--"


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

    def get_vars(self, var_dict: dict, prefix: str):
        match self:
            case Sex.NEUTER:
                for suffix, term in (("subj", "they"), ("obj", "them"), ("poss", "their")):
                    var_dict[f"{prefix}_{suffix}"] = term
                    var_dict[f"{prefix}_{suffix.capitalize()}"] = term.capitalize()
                    var_dict[f"{prefix}_{suffix.upper()}"] = term.upper()

            case Sex.MALE:
                for suffix, term in (("subj", "he"), ("obj", "him"), ("poss", "his")):
                    var_dict[f"{prefix}_{suffix}"] = term
                    var_dict[f"{prefix}_{suffix.capitalize()}"] = term.capitalize()
                    var_dict[f"{prefix}_{suffix.upper()}"] = term.upper()

            case Sex.FEMALE:
                for suffix, term in (("subj", "she"), ("obj", "her"), ("poss", "hers")):
                    var_dict[f"{prefix}_{suffix}"] = term
                    var_dict[f"{prefix}_{suffix.capitalize()}"] = term.capitalize()
                    var_dict[f"{prefix}_{suffix.upper()}"] = term.upper()


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
