from athanor.aspects import AspectSlot as _AspectSlot


class _AdventAspectSlot(_AspectSlot):
    default = None

    def load_final(self):
        if not self.aspect and self.default:
            self.set_aspect(self.default)

# Character Slots
class Race(_AdventAspectSlot):
    default = "Spirit"


class Sensei(_AdventAspectSlot):
    default = "Commoner"


class Position(_AdventAspectSlot):
    default = "Standing"


# Room Slots
class SectorType(_AdventAspectSlot):
    default = "Inside"
    key = "sector_type"


