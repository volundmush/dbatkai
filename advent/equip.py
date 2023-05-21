from evennia.utils.utils import make_iter
from athanor.equip import EquipSlot, EquipHandler


class AdventEquip(EquipSlot):
    category = "circle"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.limb = kwargs.get("limb", None)

    def is_available(self, **kwargs):
        if not self.limb:
            return True
        for l in make_iter(self.limb):
            if not self.owner.limbs.get(l):
                return False
        return True


equip_slots = {
    "right_ring_finger": {
        "wear_display": "on $pron(your) right ring finger",
        "remove_display": "from $pron(your) right ring finger",
        "slot_type": "finger",
        "list_display": "Right Ring Finger",
        "sort_order": 10,
        "limb": "right_arm"
    },

    "left_ring_finger": {
        "wear_display": "on $pron(your) left ring finger",
        "remove_display": "from $pron(your) left ring finger",
        "slot_type": "finger",
        "list_display": "Left Ring Finger",
        "sort_order": 20,
        "limb": "left_arm"
    },

    "neck_1": {
        "wear_display": "around $pron(your) neck",
        "remove_display": "from $pron(your) neck",
        "slot_type": "neck",
        "list_display": "Worn Around Neck",
        "sort_order": 30
    },

    "neck_2": {
        "wear_display": "around $pron(your) neck",
        "remove_display": "from $pron(your) neck",
        "slot_type": "neck",
        "list_display": "Worn Around Neck",
        "sort_order": 35
    },

    "body": {
        "wear_display": "around $pron(your) body",
        "remove_display": "from $pron(your) body",
        "slot_type": "body",
        "list_display": "Worn On Body",
        "sort_order": 40
    },

    "head": {
        "wear_display": "on $pron(your) head",
        "remove_display": "from $pron(your) head",
        "slot_type": "head",
        "list_display": "Worn On Head",
        "sort_order": 50
    },

    "legs": {
        "wear_display": "on $pron(your) legs",
        "remove_display": "from $pron(your) legs",
        "slot_type": "legs",
        "list_display": "Worn On Legs",
        "sort_order": 60,
        "limb": ["right_leg", "left_leg"]
    },

    "feet": {
        "wear_display": "on $pron(your) feet",
        "remove_display": "from $pron(your) feet",
        "slot_type": "feet",
        "list_display": "Worn On Feet",
        "sort_order": 70,
        "limb": ["right_leg", "left_leg"]
    },

    "hands": {
        "wear_display": "on $pron(your) hands",
        "remove_display": "from $pron(your) hands",
        "slot_type": "hands",
        "list_display": "Worn On Hands",
        "sort_order": 80,
        "limb": ["right_arm", "left_arm"]
    },

    "arms": {
        "wear_display": "on $pron(your) arms",
        "remove_display": "from $pron(your) arms",
        "slot_type": "arms",
        "list_display": "Worn On Arms",
        "sort_order": 90,
        "limb": ["right_arm", "left_arm"]
    },

    "about": {
        "wear_display": "about $pron(your) body",
        "remove_display": "from about $pron(your) body",
        "slot_type": "about",
        "list_display": "Worn About Body",
        "sort_order": 100
    },

    "waist": {
        "wear_display": "around $pron(your) waist",
        "remove_display": "from around $pron(your) waist",
        "slot_type": "waist",
        "list_display": "Worn About Waist",
        "sort_order": 110
    },

    "right_wrist": {
        "wear_display": "around $pron(your) right wrist",
        "remove_display": "from $pron(your) right wrist",
        "slot_type": "wrist",
        "list_display": "Worn On Right Wrist",
        "sort_order": 120,
        "limb": "right_arm"
    },

    "left_wrist": {
        "wear_display": "around $pron(your) left wrist",
        "remove_display": "from $pron(your) left wrist",
        "slot_type": "wrist",
        "list_display": "Worn On Left Wrist",
        "sort_order": 125,
        "limb": "left_arm"
    },

    "wield_1": {
        "wear_verb": "$conj(wields)",
        "wear_display": "as $pron(your) primary weapon",
        "remove_verb": "$conj(stops) using",
        "remove_display": "as $pron(your) primary weapon",
        "slot_type": "wield",
        "list_display": "Wielded",
        "sort_order": 130,
    },

    "wield_2": {
        "wear_verb": "$conj(holds)",
        "wear_display": "in $pron(your) offhand",
        "remove_verb": "$conj(stops) holding",
        "remove_display": "in $pron(your) offhand",
        "slot_type": "hold",
        "list_display": "Offhand",
        "sort_order": 135,
    },

    "back": {
        "wear_display": "on $pron(your) back",
        "remove_display": "from $pron(your) back",
        "slot_type": "back",
        "list_display": "Worn On Back",
        "sort_order": 140
    },

    "right_ear": {
        "wear_display": "on $pron(your) right ear",
        "remove_display": "from $pron(your) right ear",
        "slot_type": "ear",
        "list_display": "Worn on Right Ear",
        "sort_order": 150,
    },

    "left_ear": {
        "wear_display": "on $pron(your) left ear",
        "remove_display": "from $pron(your) left ear",
        "slot_type": "ear",
        "list_display": "Worn on Left Ear",
        "sort_order": 155,
    },

    "shoulders": {
        "wear_display": "on $pron(your) shoulders",
        "remove_display": "from $pron(your) shoulders",
        "slot_type": "shoulders",
        "list_display": "Worn on Shoulders",
        "sort_order": 160,
    },

    "eyes": {
        "wear_display": "over $pron(your) eyes",
        "remove_display": "from $pron(your) eyes",
        "slot_type": "eyes",
        "list_display": "Worn over Eyes",
        "sort_order": 170,
    }
}