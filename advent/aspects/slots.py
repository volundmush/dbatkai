from athanor.aspects import AspectSlot as _AspectSlot

class _AdventAspectSlot(_AspectSlot):
    pass

class Race(_AdventAspectSlot):
    default = "Spirit"


class Sensei(_AdventAspectSlot):
    default = "Commoner"
