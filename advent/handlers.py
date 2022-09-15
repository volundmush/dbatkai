from evennia.utils.utils import lazy_property
from athanor.modifiers import FlagHandler
from advent.typing import Size
import typing


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


class PercentHandler:

    def __init__(self, owner, attr_name: str, default: float = 1.0):
        self.owner = owner
        self.attr_name = attr_name
        self.data = self.owner.attributes.get(self.attr_name, default=default)

    def get(self) -> float:
        return self.data

    def set(self, value: float) -> float:
        self.data = max(0.0, min(1.0, value))
        self.owner.attributes.add(self.attr_name, self.data)
        return self.data

    def mod(self, value: float) -> float:
        return self.set(self.data + value)


class StatHandler:

    def __init__(self, owner, attr_name: str, default: int = 1):
        self.owner = owner
        self.attr_name = attr_name
        self.data = self.owner.attributes.get(self.attr_name, default=default)

    def get(self) -> int:
        return self.data

    def set(self, value: int) -> int:
        self.data = value
        self.owner.attributes.add(self.attr_name, self.data)
        return self.data

    def mod(self, value: int) -> int:
        return self.set(self.data + value)

    def mult(self) -> float:
        out = 1.0
        for m in self.owner.get_all_modifiers():
            out += m.stat_multiplier(self.owner, self.attr_name)
        return out

    def bonus(self) -> int:
        out = 0
        for m in self.owner.get_all_modifiers():
            out += m.stat_bonus(self.owner, self.attr_name)
        return out

    def get_bonuses(self) -> (int, float):
        bonus = 0
        mult = 1.0
        for m in self.owner.get_all_modifiers():
            bonus += m.stat_bonus(self.owner, self.attr_name)
            mult += m.stat_multiplier(self.owner, self.attr_name)
        return (bonus, mult)

    def effective(self) -> int:
        bonus, mult = self.get_bonuses()
        return round((self.data + bonus) * mult)


class BoundedStatHandler(StatHandler):

    def __init__(self, owner, attr_name, default: int = 1, min_amt: int = 0, max_amt = 100):
        super().__init__(owner, attr_name, default=default)
        self.min_amt = min_amt
        self.max_amt = max_amt

    def set(self, value: int) -> int:
        self.data = max(min(value, self.max_amt), self.min_amt)
        self.owner.attributes.add(self.attr_name, self.data)
        return self.data


class PowerStatHandler(StatHandler):

    def __init__(self, owner, attr_name: str, percent_name: str, default: int = 1, ):
        super().__init__(owner, attr_name, default)
        self.percent_name = percent_name

    @lazy_property
    def perc(self):
        return PercentHandler(self.owner, self.percent_name)

    def current(self) -> int:
        perc = self.perc.get()
        return round(self.effective() * perc)

    def mod_current(self, value: int):
        """
        This will adjust the underlying percent.
        """


class PowerLevelHandler(PowerStatHandler):

    def current(self) -> int:
        perc = self.perc.get()
        eff = self.effective_max()
        return eff * min(self.owner.suppress.get(), perc)

    def effective_max(self) -> int:
        eff = self.effective()
        speednar = self.owner.speednar(exist_value=eff)
        return eff * speednar


class CharacterSizeHandler(SizeHandler):

    def __init__(self, owner, default: Size = None):
        if default is None:
            default = owner.race.get().size()
        super().__init__(owner, default=default)


class PromptHandler:

    def __init__(self, owner):
        self.owner = owner

    def render(self) -> str:
        prompt_sections = list()
        prompt_sections.append(f"|W[|rPL|y: |C{self.owner.powerlevel.effective():,}|W]")
        prompt_sections.append(f"|W[|cKI|y: |C{self.owner.ki.effective():,}|W]")
        prompt_sections.append(f"|W[|gST|y: |C{self.owner.stamina.effective():,}|W]")
        return "|n".join(prompt_sections)


class LimbHandler:

    def __init__(self, owner):
        self.owner = owner
        self.data = owner.attributes.get(key="limb_condition", default=dict())

    def get(self, limb_name: str) -> int:
        return self.data.get(limb_name, 0)

    def has(self, limb_name: str) -> bool:
        return bool(self.get(limb_name))

    def reset(self):
        self.data = self.owner.race.get().get_available_limbs()
        self.save()

    def save(self):
        self.owner.attributes.add("limb_condition", self.data)

    def modify(self, limb_name: str, amt: int, create_obj=False):
        self.data[limb_name] = max(0, min(self.data[limb_name] + amt, 100))
        if not self.data[limb_name] and create_obj:
            self.create_object(limb_name)
        self.save()

    def create_object(self, limb_name: str):
        pass
