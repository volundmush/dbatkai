"""
Room

Rooms are simple containers that has no location of their own.

"""

from evennia import DefaultRoom
from evennia.utils.utils import lazy_property, list_to_string
from advent.handlers.basic import FlagsHandler, FlagHandler
from .mixins import GameObj
from evennia.utils.ansi import ANSIString
from collections import defaultdict

from rich.console import group
from rich.table import Table
from rich.text import Text
from rich.style import NULL_STYLE

from advent.utils import ev_to_rich
from advent import MODIFIERS_NAMES

COMPASS_TEMPLATE = """||{N:^3}||
||{NW:>3}|| ||{U:^3}|| ||{NE:<3}||
||{W:>3}|| ||{I:^3}|| ||{E:<3}||
||{SW:>3}|| ||{D:^3}|| ||{SE:<3}||
||{S:^3}||
"""


class Room(GameObj, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See examples/object.py for a list of
    properties and methods available on all Objects.
    """
    modifier_attrs = ["sector_type", "room_flags"]

    @lazy_property
    def room_flags(self):
        return FlagsHandler(self, "room_flags", "RoomFlags")

    @lazy_property
    def sector_type(self):
        return FlagHandler(self, "sector_type", "SectorType")

    def provides_light(self) -> bool:
        for m in self.get_all_modifiers():
            if m.is_providing_light(self):
                return True

    def is_illuminated(self) -> bool:

        # TODO: If daylight hours and room is not set dark, return true

        if self.provides_light():
            return True

        for o in self.contents:
            if o.provides_light():
                return True

    def get_planet(self):
        for m in self.room_flags.all():
            if m.planet:
                return m

    def generate_automap(self, looker, min_y=-2, max_y=2, min_x=-2, max_x=2):
        visited = set()

        cur_map = defaultdict(lambda: defaultdict(lambda: " "))

        def scan(room, cur_x, cur_y):
            if room in visited:
                return
            visited.add(room)
            if (sect := room.sector_type.get()):
                cur_map[cur_y][cur_x] = sect.map_key
            else:
                cur_map[cur_y][cur_x] = "o"

            con_map = room.get_visible_contents(looker)
            for ex_obj in con_map["exits"]:
                if not ex_obj.destination:
                    continue

                match ex_obj.key:
                    case "north":
                        if (cur_y + 1) <= max_y:
                            scan(ex_obj.destination, cur_x, cur_y + 1)
                    case "south":
                        if (cur_y - 1) >= min_y:
                            scan(ex_obj.destination, cur_x, cur_y - 1)
                    case "east":
                        if (cur_x + 1) <= max_x:
                            scan(ex_obj.destination, cur_x + 1, cur_y)
                    case "west":
                        if (cur_x - 1) >= min_x:
                            scan(ex_obj.destination, cur_x - 1, cur_y)
                    case "northeast":
                        if ((cur_y + 1) <= max_y) and ((cur_x + 1) <= max_x):
                            scan(ex_obj.destination, cur_x + 1, cur_y + 1)
                    case "northwest":
                        if ((cur_y + 1) <= max_y) and ((cur_x - 1) >= min_x):
                            scan(ex_obj.destination, cur_x - 1, cur_y + 1)
                    case "southeast":
                        if ((cur_y - 1) >= min_y) and ((cur_x + 1) <= max_x):
                            scan(ex_obj.destination, cur_x + 1, cur_y - 1)
                    case "southwest":
                        if ((cur_y - 1) >= min_y) and ((cur_x - 1) >= min_x):
                            scan(ex_obj.destination, cur_x - 1, cur_y - 1)

        scan(self, 0, 0)

        cur_map[0][0] = "|rX|n"

        return cur_map

    header_line = Text("O----------------------------------------------------------------------O")
    subheader_line = Text("------------------------------------------------------------------------")

    def generate_compass(self, looker):
        con_map = self.get_visible_contents(looker)
        compass_dict = defaultdict(str)

        for ex in con_map["exits"]:
            upper = ex.key.upper()
            match ex.key:
                case "north" | "south":
                    compass_dict[upper[0]] = f" |c{upper[0]}|n "
                case "up" | "down":
                    compass_dict[upper[0]] = f" |y{upper[0]}|n "
                case "east":
                    compass_dict["E"] = "|cE|n  "
                case "west":
                    compass_dict["W"] = "  |cW|n"
                case "northwest" | "southwest":
                    compass_dict[upper[0] + upper[5]] = f" |c{upper[0] + upper[5]}|n"
                case "northeast" | "southeast":
                    compass_dict[upper[0] + upper[5]] = f"|c{upper[0] + upper[5]}|n "
                case "inside":
                    compass_dict["I"] = f" |MI|n "
                case "outside":
                    compass_dict["I"] = "|MOUT|n"

        return ev_to_rich(COMPASS_TEMPLATE.format_map(compass_dict))

    @group()
    def return_appearance(self, looker, **kwargs):
        builder = False

        def gen_name(obj):
            return obj.get_display_name(looker=looker, pose=True, **kwargs)

        if not looker:
            return ""
        else:
            builder = self.locks.check_lockstring(looker, "perm(Builder)")

        yield self.header_line

        yield ev_to_rich(f"Location: {gen_name(self)}")

        if (planet := self.get_planet()):
            yield ev_to_rich(f"Planet: {planet}")
        yield ev_to_rich(f"Gravity: Normal")

        if builder:
            yield ev_to_rich(f"Flags: [ |g{' '.join(str(r) for r in self.room_flags.all())} |n] Sector: [ |g{self.sector_type.get()} |n ]")

        yield self.header_line

        # ourselves
        desc = self.db.desc or "You see nothing special."

        yield ev_to_rich(desc)

        yield self.subheader_line

        y_coor = [2, 1, 0, -1, -2]
        x_coor = [-4, -3, -2, -1, 0, 1, 2, 3, 4]
        automap = self.generate_automap(looker, min_x=-4, max_x=4)
        col_automap = ev_to_rich("\r\n".join(["".join([automap[y][x] for x in x_coor]) for y in y_coor]))

        map_legend = [f"{x.map_key}: {x.get_map_name()}" for x in
                      sorted(MODIFIERS_NAMES["SectorType"].values(), key=lambda y: y.mod_id)]
        map_legend.append("|rX|n: You")

        table = Table(box=None)
        table.add_column("Compass", width=17, header_style=NULL_STYLE, justify="center")
        table.add_column("Auto-Map", width=10, header_style=NULL_STYLE)
        table.add_column("Map Key", width=37, header_style=NULL_STYLE)
        table.add_row(ev_to_rich("|r---------"), ev_to_rich("|r----------"),
                      ev_to_rich("|r-----------------------------"))
        table.add_row(self.generate_compass(looker), col_automap, ev_to_rich(", ".join(map_legend)))

        yield table

        yield self.subheader_line

        # contents
        contents_map = self.get_visible_contents(looker, **kwargs)

        if (char_obj := contents_map.get("characters", None)):
            characters = ANSIString("\n").join([gen_name(obj) for obj in char_obj])
            yield ev_to_rich(characters)

        if (thing_obj := contents_map.get("things", None)):
            things = ANSIString("\n").join([gen_name(obj) for obj in thing_obj])
            yield ev_to_rich(things)

    def get_vnum_display(self):
        if hasattr(self, "legacy_room"):
            return f"|g[R-{self.legacy_room.id}]|n"
        return None
