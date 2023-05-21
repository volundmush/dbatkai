from .base import AdventAspect as _AdventAspect


class _SectorType(_AdventAspect):
    slot_type = "sector_type"
    legend = "o"


class Inside(_SectorType):
    legend = "|nI|n"


class City(_SectorType):
    legend = "|nC|n"


class Plain(_SectorType):
    legend = "|gP|n"


class Forest(_SectorType):
    legend = "|GF|n"


class Hills(_SectorType):
    legend = "|YH|n"


class Mountains(_SectorType):
    legend = "|xM|n"


class Shallows(_SectorType):
    legend = "|C~|n"


class Water(_SectorType):
    legend = "|bW|n"


class Sky(_SectorType):
    legend = "|cS|n"


class Underwater(_SectorType):
    legend = "|BU|n"


class Shop(_SectorType):
    legend = "|M$|n"


class Important(_SectorType):
    legend = "|m#|n"


class Desert(_SectorType):
    legend = "|yD|n"


class Space(_SectorType):
    pass


class Lava(_SectorType):
    legend = "|[r |n"
