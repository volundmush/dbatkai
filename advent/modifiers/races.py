from .base import Modifier as _BaseMod


class _Race(_BaseMod):
    category = "Race"
    pc_ok = True
    mimic_ok = True
    seeming_ok = True
    size = -1
    abbr = "--"
    has_seeming = False
    rpp_cost = 0


class Human(_Race):
    mod_id = 0
    abbr = "Hum"


class Saiyan(_Race):
    mod_id = 1
    abbr = "Sai"
    rpp_cost = 65


class Icer(_Race):
    mod_id = 2
    abbr = "Ice"


class Konatsu(_Race):
    mod_id = 3
    abbr = "Kon"


class Namekian(_Race):
    mod_id = 4
    abbr = "Nam"


class Mutant(_Race):
    mod_id = 5
    abbr = "Mut"


class Kanassan(_Race):
    mod_id = 6
    abbr = "Kan"


class Halfbreed(_Race):
    mod_id = 7
    abbr = "H-B"


class BioAndroid(_Race):
    mod_id = 8
    abbr = "Bio"
    seeming_ok = False


class Android(_Race):
    mod_id = 9
    abbr = "And"
    has_seeming = True


class Demon(_Race):
    mod_id = 10
    abbr = "Dem"


class Majin(_Race):
    mod_id = 11
    abbr = "Maj"


class Kai(_Race):
    mod_id = 12
    abbr = "Kai"


class Tuffle(_Race):
    mod_id = 13
    size = 4
    abbr = "Tuf"


class Hoshijin(_Race):
    mod_id = 14
    abbr = "Hos"
    mimic_ok = False
    seeming_ok = False


class Arlian(_Race):
    mod_id = 20
    abbr = "Arl"


class _NPC(_Race):
    pc_ok = False
    mimic_ok = False
    seeming_ok = False


class Animal(_NPC):
    mod_id = 15
    abbr = "Ani"


class Saiba(_NPC):
    mod_id = 16
    abbr = "Sab"
    size = 6


class Serpent(_NPC):
    mod_id = 17
    abbr = "Ser"


class Ogre(_NPC):
    mod_id = 18
    abbr = "Ogr"
    size = 6


class Yardratian(_NPC):
    mod_id = 19
    abbr = "Yar"


class Dragon(_NPC):
    mod_id = 21
    abbr = "Drg"


class Mechanical(_NPC):
    mod_id = 22
    abbr = "Mec"


class Spirit(_NPC):
    mod_id = 23
    abbr = "Spi"