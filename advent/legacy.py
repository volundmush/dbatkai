from advent.db.legacy.models import Zone, ResetCommand, MobProto, ObjProto, DgScript, LegacyRoom, LegacyShop, LegacyGuild
from advent.utils import read_json_file
from typeclasses.rooms import Room
from typeclasses.exits import Exit

from advent.typing import ExitDir
from mudrich.circle import CircleToEvennia
from evennia.utils.ansi import strip_ansi


class Importer:

    def __init__(self, caller, path):
        self.caller = caller
        self.path = path
        self.exit_info = dict()
        self.room_map = dict()
        self.account_map = dict()
        self.zone_paths = dict()
        self.zone_ids = dict()

    def msg(self, txt):
        self.caller.msg(txt)
        print(txt)

    def load_zones(self):
        z_dir = self.path / "zones"

        for d in [d for d in z_dir.iterdir() if d.is_dir()]:
            zf_dir = d / "zone.json"
            if not (zf_dir.exists() and zf_dir.is_file()):
                continue
            if not (j := read_json_file(zf_dir)):
                continue

            data = {}
            data["id"] = j["HasVnum"]["vnum"]

            if "Name" in j:
                data["color_name"] = CircleToEvennia(j["Name"])
                data["name"] = strip_ansi(data["color_name"])
            z = j["Zone"]
            if "lifespan" in z:
                data["lifespan"] = z["lifespan"]

            data["start_vnum"] = z["bot"]
            data["end_vnum"] = z["top"]

            if "age" in z:
                data["age"] = z["age"]

            if "legacy_builders" in z:
                data["legacy_builders"] = z["legacy_builders"]

            if "reset_mode" in z:
                data["reset_mode"] = z["reset_mode"]

            zone = Zone.objects.create(**data)
            self.zone_paths[zone.id] = d
            self.zone_ids[zone.id] = zone

            if "commands" in z:
                for i, c in enumerate(z["commands"]):
                    c["line"] = i + 1
                    zone.commands.create(**c)

    def load_rooms(self):
        zone_ids = Zone.objects.all().values_list("id", flat=True).order_by("id")

        exit_map = dict()
        room_map = dict()

        for zid in zone_ids:
            if zid not in [9, 3]:
                continue
            zone = self.zone_ids[zid]
            z_dir = self.zone_paths[zid]
            rf_dir = z_dir / "rooms.json"
            if not (rf_dir.exists() and rf_dir.is_file()):
                continue
            rj = read_json_file(rf_dir)
            num_rooms = len(rj)
            self.msg(f"Loading Zone {zid}, {num_rooms} rooms")

            for r in rj:
                vnum = r["HasVnum"]["vnum"]
                color_name = CircleToEvennia(r.pop("Name", f"Room {vnum}"))
                name = strip_ansi(color_name)
                ex_data = dict()
                if "Description" in r:
                    ex_data["description"] = CircleToEvennia(r.pop("Description"))

                room, errors = Room.create(key=name, **ex_data)
                if errors:
                    self.msg(errors)
                z_room = zone.rooms.create(id=vnum, obj=room)

                room.db.color_name = color_name

                if "Exits" in r:
                    exit_map[vnum] = r.pop("Exits")

                for flag in r.pop("RoomFlags", list()):
                    room.room_flags.add(flag)

                room.sector_type.set(r.pop("SectorType", 0))

        self.msg(f"Loaded {LegacyRoom.objects.count()} Rooms. Now loading exits...")

        exit_total = 0

        for rvnum, edata in exit_map.items():
            source = LegacyRoom.objects.get(id=rvnum).obj
            for direction, ed in edata:
                if not ed:
                    continue
                e_dir = ExitDir(direction)
                if (d_vnum := ed.get("to_room", None)):
                    if (dest := LegacyRoom.objects.filter(id=d_vnum).first()):
                        ex, err = Exit.create(e_dir.name.lower(), source, dest.obj)
                        if err:
                            self.msg(err)
                        exit_total += 1
                        match e_dir:
                            case ExitDir.NORTH | ExitDir.EAST | ExitDir.SOUTH | ExitDir.WEST | ExitDir.UP | ExitDir.DOWN:
                                ex.alias.add(e_dir.name.lower()[0])
                            case ExitDir.INSIDE:
                                ex.alias.add("in")
                            case ExitDir.OUTSIDE:
                                ex.alias.add("out")
                            case ExitDir.NORTHWEST | ExitDir.NORTHEAST | ExitDir.SOUTHWEST | ExitDir.SOUTHEAST:
                                low = e_dir.name.lower()
                                ex.alias.add(low[0] + low[5])
                                ex.alias.add(low[:6])


        self.msg(f"Loaded {exit_total} Exits!")

    def execute(self):

        self.msg("Importing Zones...")
        self.load_zones()
        self.msg(f"Imported {Zone.objects.count()} Zones!")

        self.msg("Importing Rooms...")
        self.load_rooms()
        self.msg(f"Imported {LegacyRoom.objects.count()} Rooms!")