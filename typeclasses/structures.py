from athanor.typeclasses.structures import AthanorStructure
from .objects import ObjectParent


class Structure(ObjectParent, AthanorStructure):
    pass


class Region(Structure):
    pass


class PlayerHouse(Structure):
    pass


class PocketDimension(Structure):
    pass


class SpaceStation(Structure):
    pass


class SpaceShip(Structure):
    pass


class Space(Region):
    pass


class Existence(Structure):
    pass


class Universe(Structure):
    pass


class Dimension(Region):
    pass


class CelestialBody(Structure):
    """
    Abstract class. Don't instantiate directly.
    """


class Planet(CelestialBody):
    pass


class Moon(CelestialBody):
    pass


class Asteroid(CelestialBody):
    pass
