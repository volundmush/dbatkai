r"""
Evennia settings file.

The available options are found in the default settings file found
here:

/home/volund/PycharmProjects/evennia/evennia/settings_default.py

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from athanor.settings import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "Dragon Ball Advent Truth"


######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")


INSTALLED_APPS.extend([
    "advent.legacy",
])


MODIFIER_PATHS.extend([
    "advent.modifiers.admin_flags",
    "advent.modifiers.affects",
    "advent.modifiers.bonuses",
    "advent.modifiers.item_flags",
    "advent.modifiers.item_types",
    "advent.modifiers.mob_flags",
    "advent.modifiers.player_flags",
    "advent.modifiers.positions",
    "advent.modifiers.preference_flags",
    "advent.modifiers.races",
    "advent.modifiers.room_flags",
    "advent.modifiers.room_sectors",
    "advent.modifiers.sensei",
    "advent.modifiers.wear_flags",
    "advent.modifiers.zone_flags",
    "advent.modifiers.genomes",
    "advent.modifiers.mutations",
    "advent.modifiers.android",
    "advent.modifiers.transformations"
])

BASE_CHARACTER_TYPECLASS = "typeclasses.characters.PlayerCharacter"

BASE_ZONE_TYPECLASS = "advent.legacy.zones.DefaultZone"

SYSTEMS.extend([
    "advent.systems.ZoneSystem",
])

MAX_NR_CHARACTERS = 10

DG_FUNCTIONS["shared"].extend([
    "advent.dgscripts.shared"
])

DG_FUNCTIONS["character"].extend([
    "advent.dgscripts.character"
])

DG_FUNCTIONS["item"].extend([
    "advent.dgscripts.item"
])

DG_FUNCTIONS["room"].extend([

])

SEARCH_MULTIMATCH_REGEX = r"^(?:(?P<number>(\d+|all|\*))\.)?(?P<name>.+?)(?: +(?P<args>.+)?)?$"

SEARCH_MULTIMATCH_TEMPLATE = " {number}.{name} - {aliases} - {info}\n"

SEARCH_AT_RESULT = "advent.utils.at_search_result"

PROTOTYPE_MODULES.extend([
    "world.proto_legacy_items",
    "world.proto_legacy_mobs"
])


EQUIP_CLASS_PATHS.extend([
    "advent.equip"
])

CHARACTER_COMMAND_PATHS = [
    "commands.char_info",
    "commands.char_item",
    "commands.char_other"
]