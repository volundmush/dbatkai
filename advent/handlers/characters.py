from evennia.utils.utils import lazy_property
from .basic import SizeHandler, FlagHandler
from advent.typing import Size
import typing


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
