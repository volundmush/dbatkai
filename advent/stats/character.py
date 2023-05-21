from athanor.stats import Stat as _Stat


class _CharacterStat(_Stat):
    category = "character"


class PowerLevel(_CharacterStat):

    def default(self) -> float:
        return 5.0

    def base_value(self) -> float:
        return self.owner.attributes.get(key="basepl", default=self.default())

    def get_effective_base_pl(self):
        if self.owner.db.multi_owner:
            return self.owner.db.multi_owner.stats.stats["PowerLevel"].get_effective_base_pl()
        else:
            return self.base_value() / 1 + len(self.owner.attributes.get(key="clones", default=[]))

    def get_true_max_pl(self):
        return (self.get_effective_base_pl() + self.calculate_modifier("pl_pre_mult")) * (1.0 * self.calculate_modifier("pl_mult")) + self.calculate_modifier("pl_post_mult")

    def get_max_pl(self):
        total = self.get_true_max_pl()
        if (kaioken := self.calculate_modifier("kaioken")):
            total += (total / 10) * kaioken
        if (dark_meta := self.calculate_modifier("dark_meta")):
            total *= 1.6
        return total

    def get_effective_max_pl(self):
        return self.get_max_pl() * self.handler.get_effective("speednar", clear=False)

    def calculate(self) -> float:
        if (suppress := self.calculate_modifier("suppress")):
            return self.get_effective_max_pl() * min(suppress / 100.0, self.handler.get_effective("health", clear=False) / 100.0)
        else:
            return self.get_effective_max_pl() * self.handler.get_effective("health", clear=False) / 100.0