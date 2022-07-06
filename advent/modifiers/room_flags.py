from .base import Modifier as _BaseMod


class _RoomFlag(_BaseMod):
    category = "RoomFlags"
    mod_id = -1
    planet = False


class Dark(_RoomFlag):
    mod_id = 0

    def is_providing_darkness(self, obj) -> bool:
        return True


class Death(_RoomFlag):
    mod_id = 1


class NoMob(_RoomFlag):
    mod_id = 2


class Indoors(_RoomFlag):
    mod_id = 3


class Peaceful(_RoomFlag):
    mod_id = 4


class Soundproof(_RoomFlag):
    mod_id = 5


class NoTrack(_RoomFlag):
    mod_id = 6


class NoInstant(_RoomFlag):
    mod_id = 7


class Tunnel(_RoomFlag):
    mod_id = 8


class Private(_RoomFlag):
    mod_id = 9


class GodRoom(_RoomFlag):
    mod_id = 10


class House(_RoomFlag):
    mod_id = 11


class HouseCrash(_RoomFlag):
    mod_id = 12


class Atrium(_RoomFlag):
    mod_id = 13


class OLC(_RoomFlag):
    mod_id = 14


class BFSMark(_RoomFlag):
    mod_id = 15


class Vehicle(_RoomFlag):
    mod_id = 16


class Underground(_RoomFlag):
    mod_id = 17


class Current(_RoomFlag):
    mod_id = 18


class TimedDeathtrap(_RoomFlag):
    mod_id = 19


class Earth(_RoomFlag):
    mod_id = 20
    planet = True


class Vegeta(_RoomFlag):
    mod_id = 21
    planet = True


class Frigid(_RoomFlag):
    mod_id = 22
    planet = True


class Konack(_RoomFlag):
    mod_id = 23
    planet = True


class Namek(_RoomFlag):
    mod_id = 24
    planet = True


class Neo(_RoomFlag):
    mod_id = 25


class Afterlife(_RoomFlag):
    mod_id = 26


class Space(_RoomFlag):
    mod_id = 27


class Hell(_RoomFlag):
    mod_id = 28


class Regen(_RoomFlag):
    mod_id = 29


class RHell(_RoomFlag):
    mod_id = 30


class GravityX10(_RoomFlag):
    mod_id = 31


class Aether(_RoomFlag):
    mod_id = 32
    planet = True


class HBTC(_RoomFlag):
    mod_id = 33


class Past(_RoomFlag):
    mod_id = 34


class ClanBank(_RoomFlag):
    mod_id = 35


class Ship(_RoomFlag):
    mod_id = 36


class Yardrat(_RoomFlag):
    mod_id = 37
    planet = True


class Kanassa(_RoomFlag):
    mod_id = 38
    planet = True


class Arlia(_RoomFlag):
    mod_id = 39
    planet = True


class Aura(_RoomFlag):
    mod_id = 40


class EarthOrbit(_RoomFlag):
    mod_id = 41


class FrigidOrbit(_RoomFlag):
    mod_id = 42


class KonackOrbit(_RoomFlag):
    mod_id = 43


class NamekOrbit(_RoomFlag):
    mod_id = 44


class VegetaOrbit(_RoomFlag):
    mod_id = 45


class AetherOrbit(_RoomFlag):
    mod_id = 46


class YardratOrbit(_RoomFlag):
    mod_id = 47


class KanassaOrbit(_RoomFlag):
    mod_id = 48


class ArliaOrbit(_RoomFlag):
    mod_id = 49


class Nebulae(_RoomFlag):
    mod_id = 50


class Asteroid(_RoomFlag):
    mod_id = 51


class Wormhole(_RoomFlag):
    mod_id = 52


class Station(_RoomFlag):
    mod_id = 53


class Star(_RoomFlag):
    mod_id = 54


class Cerria(_RoomFlag):
    mod_id = 55
    planet = True


class CerriaOrbit(_RoomFlag):
    mod_id = 56


class Bedroom(_RoomFlag):
    mod_id = 57


class Workout(_RoomFlag):
    mod_id = 58


class Garden1(_RoomFlag):
    mod_id = 59


class Garden2(_RoomFlag):
    mod_id = 60


class Fertile1(_RoomFlag):
    mod_id = 61


class Fertile2(_RoomFlag):
    mod_id = 62


class Fishing(_RoomFlag):
    mod_id = 63


class FishFresh(_RoomFlag):
    mod_id = 64


class CanRemodel(_RoomFlag):
    mod_id = 65