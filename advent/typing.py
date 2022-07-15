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


class WearSlot(IntEnum):
    FINGER_RIGHT = 1
    FINGER_LEFT = 2
    NECK_1 = 3
    NECK_2 = 4
    BODY = 5
    HEAD = 6
    LEGS = 7
    FEET = 8
    HANDS = 9
    ARMS = 10
    ABOUT = 12
    WAIST = 13
    WRIST_RIGHT = 14
    WRIST_LEFT = 15
    WIELD_1 = 16
    WIELD_2 = 17
    BACK = 18
    EAR_RIGHT = 19
    EAR_LEFT = 20
    SHOULDERS = 21
    EYE = 22

    def display(self):
        match self:
            case WearSlot.FINGER_RIGHT:
                return "Worn On Right Finger"
            case WearSlot.FINGER_LEFT:
                return "Worn On Left Finger"
            case WearSlot.NECK_1 | WearSlot.NECK_2:
                return "Worn Around Neck"
            case WearSlot.BODY | WearSlot.HEAD | WearSlot.LEGS | WearSlot.FEET | WearSlot.HANDS | WearSlot.ARMS | WearSlot.SHOULDERS | WearSlot.EYE:
                return f"Worn On {self.name.capitalize()}"
            case WearSlot.ABOUT:
                return "Worn About Body"
            case WearSlot.WAIST:
                return "Worn About Waist"
            case WearSlot.WRIST_RIGHT:
                return "Worn On Right Wrist"
            case WearSlot.WRIST_LEFT:
                return "Worn On Left Wrist"
            case WearSlot.WIELD_1:
                return "Wielded"
            case WearSlot.WIELD_2:
                return "Offhand"
            case WearSlot.BACK:
                return "Worn On Back"
            case WearSlot.EAR_RIGHT:
                return "Worn On Right Ear"
            case WearSlot.EAR_LEFT:
                return "Worn On Right Ear"
