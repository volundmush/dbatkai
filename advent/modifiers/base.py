
class Modifier:
    mod_id = -1

    def __init__(self, owner):
        self.owner = owner

    @classmethod
    def get_name(cls):
        if hasattr(cls, "name"):
            return cls.name
        return cls.__name__

    def __str__(self):
        if hasattr(self.__class__, "name"):
            return self.name
        return self.__class__.__name__

    def __int__(self):
        return self.mod_id

    def __repr__(self):
        return f"<{self.__class__.__name__}: {int(self)}>"

    def is_providing_light(self, obj) -> bool:
        return False

    def is_providing_darkness(self, obj) -> bool:
        return False

    def provides_gravity_tolerance(self, obj) -> int:
        return 0
