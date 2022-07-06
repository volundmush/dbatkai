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
from evennia.settings_default import *

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
    "advent.db.legacy"
])


MODIFIER_PATHS = [
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
]

BASE_CHARACTER_TYPECLASS = "typeclasses.characters.PlayerCharacter"


MULTISESSION_MODE = 3
# The maximum number of characters allowed by the default ooc char-creation command
MAX_NR_CHARACTERS = 10


SERVER_SESSION_CLASS = "advent.serversession.AdventSession"

CMD_IGNORE_PREFIXES = ""