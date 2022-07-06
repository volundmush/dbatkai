from advent import MODIFIERS_NAMES, MODIFIERS_ID, PENDING_COMMANDS
import typing
from advent.utils import partial_match
from advent.exceptions import DatabaseError
from advent.typing import Size


class FlagHandler:
    """
    Class used as a base for handling single Modifier types, like Race, Sensei, ItemType, RoomSector.
    """

    def __init__(self, owner, attr_name, mod_category: str, default=0):
        """
        Set up the FlagsHandler.

        Args:
            owner (ObjectDB): The game object that'll have the flag.
            attr_name: The attribute that'll be used to store the flag ID.
            mod_category: The category index for MODIFIERS_NAMES[idx] and MODIFIERS_ID[idx]
        """
        self.owner = owner
        self.attr_name = attr_name
        self.mod_category = mod_category
        self.modifier = None
        self.default = default
        self.load()

    def load(self):
        data = self.owner.attributes.get(self.attr_name, default=self.default)
        if (found := MODIFIERS_ID[self.mod_category].get(data, None)):
            self.modifier = found(self.owner)

    def get(self) -> typing.Optional["Modifier"]:
        return self.modifier

    def all(self):
        if self.modifier:
            return [self.modifier]
        return []

    def set(self, flag: typing.Union[int, str, typing.Type["Modifier"]], strict: bool = False):
        """
        Used to set a flag to owner. It will replace existing one.

        Args:
            flag (int or str): ID or name (case insensitive) of flag.
            strict (bool): raise error if flag doesn't exist.

        Raises:
            DatabaseError if flag does not exist.
        """
        if hasattr(flag, "mod_id"):
            self.modifier = flag(self.owner)
            self.save()
            return self.modifier

        if isinstance(flag, int):
            if (found := MODIFIERS_ID[self.mod_category].get(flag, None)):
                self.modifier = found(self.owner)
                self.save()
                return self.modifier
        if isinstance(flag, str):
            if (fname := partial_match(flag, MODIFIERS_NAMES[self.mod_category].keys())):
                found = MODIFIERS_NAMES[self.mod_category][fname]
                self.modifier = found(self.owner)
                self.save()
                return self.modifier
        if strict:
            raise DatabaseError(f"{self.mod_category} {flag} not found!")

    def save(self):
        if self.modifier:
            self.owner.attributes.add(self.attr_name, self.modifier.mod_id)
        else:
            self.owner.attributes.remove(self.attr_name)

    def clear(self):
        self.modifier = None
        self.save()


class FlagsHandler:
    """
    Class used as a base for handling PlayerFlags, RoomFlags, MobFlags, and similar.

    It is meant to be instantiated via @lazy_property on an ObjectDB typeclass.

    These are objects loaded into advent.MODIFIERS_NAMES and MODIFIERS_ID.
    """

    def __init__(self, owner, attr_name: str, mod_category: str):
        """
        Set up the FlagsHandler.

        Args:
            owner (ObjectDB): The game object that'll have the flags.
            attr_name: The attribute that'll be used to store the flag IDs.
            mod_category: The category index for MODIFIERS_NAMES[idx] and MODIFIERS_ID[idx]
        """
        self.owner = owner
        self.attr_name = attr_name
        self.mod_category = mod_category
        self.modifiers_names = dict()
        self.modifiers_ids = dict()
        self.load()

    def load(self):
        """
        Called by init. Retrieves IDs from attribute and references against the loaded
        modifiers.
        """
        data = self.owner.attributes.get(self.attr_name, default=list())
        found = [fo for f in data if (fo := MODIFIERS_ID[self.mod_category].get(f, None))]
        for f in found:
            m = f(self.owner)
            self.modifiers_ids[m.mod_id] = m
            self.modifiers_names[str(m)] = m

    def save(self):
        """
        Serializes and sorts the Modifier IDs and saves to Attribute.
        """
        self.owner.attributes.add(self.attr_name, sorted(self.modifiers_ids.keys()))

    def has(self, flag: typing.Union[int, str, typing.Type["Modifier"]]) -> bool:
        """
        Called to determine if owner has this flag.

        Args:
            flag (int or str): ID or name (case insensitive) of flag.

        Returns:
            answer (bool): Whether owner has flag.
        """
        if hasattr(flag, "mod_id"):
            flag = flag.mod_id
        if isinstance(flag, int) and flag in self.modifiers_ids:
            return True
        if isinstance(flag, str) and partial_match(flag, self.modifiers_names.keys(), exact=True):
            return True
        return False

    def all(self) -> typing.Iterable["Modifier"]:
        """
        Get all Flags of this type on owner.
        Largely useful for iteration.

        Returns:
            List of modifiers.
        """
        return list(self.modifiers_ids.values())

    def add(self, flag: typing.Union[int, str, typing.Type["Modifier"]], strict=False):
        """
        Used to add a flag to owner.

        Args:
            flag (int or str): ID or name (case insensitive) of flag.
            strict (bool): raise error if flag doesn't exist.

        Raises:
            DatabaseError if flag does not exist.
        """
        if hasattr(flag, "mod_id"):
            m = flag(self.owner)
            self.modifiers_ids[m.mod_id] = m
            self.modifiers_names[str(m)] = m
            self.save()
            return

        if isinstance(flag, int):
            if (found := MODIFIERS_ID[self.mod_category].get(flag, None)):
                m = found(self.owner)
                self.modifiers_ids[m.mod_id] = m
                self.modifiers_names[str(m)] = m
                self.save()
                return
        if isinstance(flag, str):
            if (fname := partial_match(flag, MODIFIERS_NAMES[self.mod_category].keys())):
                found = MODIFIERS_NAMES[self.mod_category][fname]
                m = found(self.owner)
                self.modifiers_ids[m.mod_id] = m
                self.modifiers_names[str(m)] = m
                self.save()
                return
        if strict:
            raise DatabaseError(f"{self.mod_category} {flag} not found!")

    def remove(self, flag: typing.Union[int, str], strict=False):
        """
        Removes a flag if owner has it.

        Args:
            flag (int or str): ID or name (case insensitive) of flag.
            strict (bool): raise error if flag doesn't exist.

        Raises:
            DatabaseError if flag does not exist.
        """
        if isinstance(flag, int):
            if (found := self.modifiers_ids.pop(flag, None)):
                self.modifiers_names.pop(str(found))
                self.save()
                return
        if isinstance(flag, str):
            if (found := partial_match(flag, self.modifiers_ids.values(), exact=True)):
                self.modifiers_ids.pop(found.mod_id, None)
                self.modifiers_names.pop(str(found), None)
                self.save()
                return
        if strict:
            raise DatabaseError(f"{self.mod_category} {flag} not found!")


class InventoryHandler:
    attr_name = "inventory"

    def __init__(self, owner):
        self.owner = owner
        self.data = None
        self.load()

    def load(self):
        if not self.owner.attributes.has(self.attr_name):
            self.owner.attributes.add(self.attr_name, list())
        self.data = self.owner.attributes.get(self.attr_name)

    def all(self):
        return list(self.data)

    def add(self, obj):
        self.data.append(obj)

    def remove(self, obj):
        if obj in self.data:
            self.data.remove(obj)

    def dump(self):
        contents = self.all()
        self.data.clear()
        return contents


class EquipmentHandler:
    attr_name = "equipment"
    reverse_name = "equipped"

    def __init__(self, owner):
        self.owner = owner
        self.data = None
        self.load()

    def load(self):
        if not self.owner.attributes.has(self.attr_name):
            self.owner.attributes.add(self.attr_name, dict())
        self.data = self.owner.attributes.get(self.attr_name)

    def all(self):
        return list(self.data.values())

    def get(self, slot: int):
        return self.data.get(slot, None)

    def equip(self, slot: int, obj):
        self.data[slot] = obj
        obj.location = self.owner
        obj.attributes.add(self.reverse_name, (slot, self.owner))

    def remove(self, slot: int):
        found = self.data.pop(slot, None)
        if found:
            found.attributes.remove(self.reverse_name)
        return found


class WeightHandler:
    attr_name = "weight"

    def __init__(self, owner):
        self.owner = owner
        self.data = None
        self.load()

    def load(self):
        if not self.owner.attributes.has(self.attr_name):
            self.owner.attributes.add(self.attr_name, 0.0)
        self.data = self.owner.attributes.get(self.attr_name)

    def set(self, value: float):
        self.data = value
        self.save()

    def get_bonuses(self) -> (int, float):
        bonus = 0
        mult = 1.0
        for m in self.owner.get_all_modifiers():
            bonus += m.stat_bonus(self.owner, self.attr_name)
            mult += m.stat_multiplier(self.owner, self.attr_name)
        return (bonus, mult)

    def personal(self):
        bonus, mult = self.get_bonuses()
        return (self.data + bonus) * mult

    def get(self) -> float:
        return self.data

    def save(self):
        self.owner.attributes.add(self.attr_name, self.data)

    def total(self) -> float:
        return self.personal() + self.burden()

    def burden(self) -> float:
        return self.equipped() + self.carried()

    def equipped(self) -> float:
        out = 0.0
        if hasattr(self.owner, "equipment"):
            for o in self.owner.equipment.all():
                out += o.weight.total()
        return out

    def carried(self) -> float:
        out = 0.0
        if hasattr(self.owner, "inventory"):
            for o in self.owner.inventory.all():
                out += o.weight.total()
        return out


class SizeHandler:
    attr_name = "size"

    def __init__(self, owner, default: Size = Size.MEDIUM):
        self.owner = owner
        self.data = owner.attributes.get(self.attr_name, default)

    def get(self) -> Size:
        return self.data

    def set(self, value: typing.Union[Size, int]):
        self.data = Size(value)
        self.owner.attributes.add(self.attr_name, self.data)


class ExDescription:
    attr_name = "ex_descriptions"


class CmdQueueHandler:

    def __init__(self, owner):
        self.owner = owner
        self.queue = list()
        self.wait_time = 0.0

    def add(self, cmd):
        self.queue.append(cmd)
        PENDING_COMMANDS.add(self.owner)

    def clear(self):
        if self.queue:
            self.queue.clear()
            return True
        return False

    def execute(self):
        if self.queue:
            try:
                cmd = self.queue.pop(0)
                cmd.parse()
                if not cmd.can_perform_command():
                    return
                cmd.func()
                cmd.at_post_cmd()
            except Exception as err:
                self.owner.msg(err)

    def check(self, decrement: float) -> bool:
        self.wait_time = max(0.0, self.wait_time - decrement)
        if self.wait_time <= 0:
            self.execute()
        return bool(self.queue)

    def set_wait(self, wait_time: float = 0.0):
        self.wait_time = wait_time


class PromptHandler:

    def __init__(self, owner):
        self.owner = owner

    def render(self) -> str:
        return "[NOT IMPLEMENTED]"
