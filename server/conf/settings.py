r"""
Evennia settings file.

The available options are found in the default settings file found
here:

C:\Users\basti\PycharmProjects\evennia\evennia\settings_default.py

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
SERVERNAME = "Dragon Ball Advent Truth Kai"

# Typeclass for account objects (linked to a character) (fallback)
BASE_ACCOUNT_TYPECLASS = "typeclasses.accounts.Account"
# Typeclass and base for all objects (fallback)
BASE_OBJECT_TYPECLASS = "typeclasses.objects.Object"
BASE_ITEM_TYPECLASS = BASE_OBJECT_TYPECLASS
# Typeclass for character objects linked to an account (fallback)
BASE_CHARACTER_TYPECLASS = "typeclasses.characters.PlayerCharacter"
# Typeclass for rooms (fallback)
BASE_ROOM_TYPECLASS = "typeclasses.rooms.Room"
# Typeclass for Exit objects (fallback).
BASE_EXIT_TYPECLASS = "typeclasses.exits.Exit"
# Typeclass for Channel (fallback).
BASE_CHANNEL_TYPECLASS = "typeclasses.channels.Channel"
# Typeclass for Scripts (fallback). You usually don't need to change this
# but create custom variations of scripts on a per-case basis instead.
BASE_SCRIPT_TYPECLASS = "typeclasses.scripts.Script"


BASE_NPC_TYPECLASS = "typeclasses.characters.NonPlayerCharacter"
BASE_SECTOR_TYPECLASS = "athanor.typeclasses.sectors.AthanorSector"
BASE_GRID_TYPECLASS = "athanor.typeclasses.grids.AthanorGrid"
BASE_STRUCTURE_TYPECLASS = "athanor.typeclasses.structures.AthanorStructure"


######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")

DG_INSTANCE_CLASSES = dict()

DG_VARS = ["advent.dgscripts.dgvars"]

DG_FUNCTIONS = ["advent.dgscripts.dgfuncs"]

ASPECT_SLOT_CLASS_PATHS.append("advent.aspects.slots")
ASPECT_CLASS_PATHS.extend(["advent.aspects.race", "advent.aspects.subrace", "advent.aspects.sensei",
                           "advent.aspects.position", "advent.aspects.sector_type"])

QUIRK_SLOT_CLASS_PATHS.append("advent.quirks.slots")
QUIRK_CLASS_PATHS.extend(["advent.quirks.bonuses", "advent.quirks.flaws"])