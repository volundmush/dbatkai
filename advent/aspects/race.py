from .base import AdventAspect as _AdventAspect


class _Race(_AdventAspect):
    slot_type = "race"

    @classmethod
    def get_key(cls):
        return getattr(cls, "key", cls.__name__.lower())


class Human(_Race):
    pass


class Saiyan(_Race):
    pass


class Icer(_Race):
    pass


class Konatsu(_Race):
    pass


class Namekian(_Race):
    pass


class Mutant(_Race):
    pass


class Kanassan(_Race):
    pass


class HalfSaiyan(_Race):
    key = "Half-Saiyan"


class BioAndroid(_Race):
    key = "Bio-Android"


class Android(_Race):
    pass

class Demon(_Race):
    pass


class Majin(_Race):
    pass


class Kai(_Race):
    pass


class Tuffle(_Race):
    pass


class Hoshijin(_Race):
    pass


class Animal(_Race):
    pass


class Saiba(_Race):
    pass


class Serpent(_Race):
    pass


class Ogre(_Race):
    pass

class Yardratian(_Race):
    pass


class Arlian(_Race):
    pass


class Dragon(_Race):
    pass


class Mechanical(_Race):
    pass


class Spirit(_Race):
    pass
