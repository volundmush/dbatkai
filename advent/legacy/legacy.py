from athanor.dgscripts.dgscripts import DefaultDGScript
from advent.legacy.models import LegacyRoom, LegacyShop, LegacyGuild
from advent.legacy.zones import DefaultZone
from advent.utils import read_json_file
from typeclasses.rooms import Room
from typeclasses.exits import Exit
from typeclasses.items import Item
from typeclasses.accounts import Account
from collections import defaultdict
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from pathlib import Path

_email = EmailValidator()

from athanor.typing import ExitDir
from advent.typing import Size, Sex
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
        self.pc_map = dict()
        self.majin_map = dict()
        proto_file = Path("world") / "prototypes.py"
        self.proto_file = open(proto_file, mode="a")
        self.proto_file.write("from athanor.typing import ExitDir\n")
        self.proto_file.write("from advent.typing import Size, Sex\n\n")

    def msg(self, txt):
        self.caller.msg(txt)
        print(txt)

    def _load_item(self, j: dict) -> Item:

        key = strip_ansi(CircleToEvennia(j.pop("key")))

        for t in ("desc", "color_name", "room_description"):
            if t in j:
                j[t] = CircleToEvennia(j[t])

        if "size" in j:
            j["size"] = Size(j["size"])

        if "ex_descriptions" in j:
            j["ex_descriptions"] = [[keyword, CircleToEvennia(desc)] for keyword, desc in j.pop("ex_descriptions")]

        contents = j.pop("contents", list())

        attributes = [[k, v] for k, v in j.items()]

        obj, errors = Item.create(key, attributes=attributes)
        if errors:
            self.msg(errors)

        for o in contents:
            held = self._load_item(o)
            held.location = obj
            obj.inventory.add(held)

        return obj


    def load_characters(self):
        c_dir = self.path / "characters"
        count = 0
        if not (c_dir.exists() and c_dir.is_dir()):
            return

        for d in [d for d in c_dir.iterdir() if d.is_file()]:
            if not (j := read_json_file(d)):
                continue
            count += 1
            p_specials = j.pop("player_specials")
            acc_id = p_specials.pop("account_id")
            acc = self.account_map[acc_id]
            data = {}

            data["location"] = None

            data["key"] = j.pop("key")

            self.msg(f"Creating {acc.key}'s character: {data['key']}")

            for t in ("desc", "color_name", "room_description"):
                if t in j:
                    j[t] = CircleToEvennia(j[t])

            if "size" in j:
                j["size"] = Size(j["size"])

            if "sex" in j:
                j["sex"] = Sex(j["sex"])

            if "skills" in j:
                j["skills"] = {k: v for k, v in j["skills"]}

            if "prelogout_location" in j:
                if (found := LegacyRoom.objects.filter(id=j["prelogout_location"]).first()):
                    j["prelogout_location"] = found.obj

            carrying = j.pop("carrying", list())
            equipment = j.pop("equipment", list())

            if "global_vars" in j:
                vars = defaultdict(dict)
                for varname, context, value in j.pop("global_vars"):
                    vars[context][varname] = value
                j["dgscript_vars"] = dict(vars)

            majinizer = j.pop("majinizer", None)

            data["attributes"] = [[k, v] for k, v in j.items()]

            c, err = acc.create_character(**data)
            if err:
                self.msg(err)

            self.pc_map[j["player_id"]] = c
            if majinizer:
                self.majin_map[c] = majinizer

            for v in carrying:
                o = self._load_item(v)
                o.location = c
                c.inventory.add(o)

            for k, v in equipment:
                o = self._load_item(v)
                o.location = c
                c.equipment.equip(k, o)

        for k, v in self.majin_map:
            if (found := self.pc_map.get(v, None)):
                k.db.majinizer = found

        return count

    def load_accounts(self):
        a_dir = self.path / "accounts"
        count = 0
        if not (a_dir.exists() and a_dir.is_dir()):
            return

        for d in [d for d in a_dir.iterdir() if d.is_file()]:
            if not (j := read_json_file(d)):
                continue
            count += 1
            acc_id = j.pop("account_id")
            data = {
                "username": j.pop("name"),
                "password": "OogieBoogiePortal2"
            }
            if "email" in j:
                try:
                    email = j.pop("email")
                    _email(email)
                    data["email"] = email
                except ValidationError as err:
                    pass
            should_super = False
            if data["username"] in ("Wayland", "Virtus", "Set", "Gorf"):
                data["permissions"] = "Developer"
                should_super = True
            elif "supervisor_level" in j:
                super_level = j.pop("supervisor_level")
                if super_level:
                    data["permissions"] = "Admin"
            self.msg(f"Creating Account: {data['username']}")
            acc, errors = Account.create(**data)
            if errors:
                self.msg(errors)
            acc.set_password(j.pop("password"))
            if should_super:
                acc.is_superuser = True
            acc.save()

            for k, v in j.items():
                acc.attributes.add(k, v)

            self.account_map[acc_id] = acc

        return count

    def load_zones(self):
        z_dir = self.path / "zones"

        for d in [d for d in z_dir.iterdir() if d.is_dir()]:
            zf_dir = d / "zone.json"
            if not (zf_dir.exists() and zf_dir.is_file()):
                continue
            if not (j := read_json_file(zf_dir)):
                continue

            data = {}
            cdict = {}
            cdict["id"] = j["HasVnum"]["vnum"]

            data["color_name"] = CircleToEvennia(j.pop("Name", "Nameless Zone"))
            cdict["db_key"] = strip_ansi(data["color_name"])

            self.msg(f"Loading Zone {cdict['id']}: {cdict['db_key']}")

            z = j["Zone"]
            if "lifespan" in z:
                cdict["db_lifespan"] = z["lifespan"]

            cdict["db_start_vnum"] = z["bot"]
            cdict["db_end_vnum"] = z["top"]

            if "legacy_builders" in z:
                data["legacy_builders"] = z["legacy_builders"]

            if "reset_mode" in z:
                cdict["db_reset_mode"] = z["reset_mode"]

            zone = DefaultZone.objects.create(**cdict)
            zone.save()
            for k, v in data.items():
                zone.attributes.add(k, v)

            zone.db.legacy_path = d

            self.zone_paths[zone.id] = d
            self.zone_ids[zone.id] = zone

            if "commands" in z:
                for i, c in enumerate(z["commands"]):
                    c["line"] = i + 1
                    zone.commands.create(**c)

    def load_mobiles(self):
        # first, create a base prototype for everything.
        proto = {
            "prototype_key": "formless_mobile",
            "prototype_desc": "The base prototype for all mobiles.",
            "prototype_tags": ["legacy_mobile", "legacy", "legacy_base"],
            "prototype_locks": "edit:superuser()",
            "typeclass": "typeclasses.characters.NonPlayerCharacter"
        }

        self.proto_file.write(f"{proto['prototype_key']} = {repr(proto)}\n\n")

        #save_prototype(proto)
        count = 0
        zone_ids = DefaultZone.objects.all().values_list("id", flat=True).order_by("id")

        for zid in zone_ids:
            zone = self.zone_ids[zid]
            z_dir = self.zone_paths[zid]
            f_dir = z_dir / "mobiles.json"

            if not (f_dir.exists() and f_dir.is_file()):
                continue
            rj = read_json_file(f_dir)
            num_things = len(rj)
            self.msg(f"Loading Zone {zid}: {zone.name}, {num_things} Mobiles")

            for j in rj:
                count += 1
                vnum = j.pop("vnum")
                j["prototype_key"] = f"legacy_mobile_{vnum}"
                j["prototype_parent"] = "formless_mobile"
                j["prototype_tags"] = ["legacy_mobile", "legacy"]

                for t in ("desc", "color_name", "room_description"):
                    if t in j:
                        j[t] = CircleToEvennia(j[t])

                #if "size" in j:
                #    j["size"] = Size(j["size"])

                #if "sex" in j:
                #    j["sex"] = Sex(j["sex"])

                self.proto_file.write(f"{j['prototype_key']} = {repr(j)}\n\n")
                #save_prototype(j)

        return count

    def load_items(self):

        # first, create a base prototype for everything.
        proto = {
            "prototype_key": "formless_item",
            "prototype_desc": "The base item for all items.",
            "prototype_tags": ["legacy_item", "legacy", "legacy_base"],
            "prototype_locks": "edit:superuser()",
            "typeclass": "typeclasses.items.Item"
        }

        self.proto_file.write(f"{proto['prototype_key']} = {repr(proto)}\n\n")

        #save_prototype(proto)
        count = 0

        zone_ids = DefaultZone.objects.all().values_list("id", flat=True).order_by("id")

        for zid in zone_ids:
            zone = self.zone_ids[zid]
            z_dir = self.zone_paths[zid]
            f_dir = z_dir / "objects.json"

            if not (f_dir.exists() and f_dir.is_file()):
                continue
            rj = read_json_file(f_dir)
            num_things = len(rj)
            self.msg(f"Loading Zone {zid}: {zone.name}, {num_things} Items")

            for j in rj:
                count += 1
                vnum = j.pop("vnum")
                j["prototype_key"] = f"legacy_item_{vnum}"
                j["prototype_parent"] = "formless_item"
                j["prototype_tags"] = ["legacy_item", "legacy"]

                for t in ("desc", "color_name", "room_description"):
                    if t in j:
                        j[t] = CircleToEvennia(j[t])

                #if "size" in j:
                #    j["size"] = Size(j["size"])

                if "ex_descriptions" in j:
                    j["ex_descriptions"] = [[keyword, CircleToEvennia(desc)] for keyword, desc in j.pop("ex_descriptions")]

                self.proto_file.write(f"{j['prototype_key']} = {repr(j)}\n\n")

                #save_prototype(j)

        return count

    def load_dgscripts(self):
        zone_ids = DefaultZone.objects.all().values_list("id", flat=True).order_by("id")

        for zid in zone_ids:
            zone = self.zone_ids[zid]
            z_dir = self.zone_paths[zid]
            f_dir = z_dir / "triggers.json"

            if not (f_dir.exists() and f_dir.is_file()):
                continue
            rj = read_json_file(f_dir)
            num_things = len(rj)
            self.msg(f"Loading Zone {zid}: {zone.name}, {num_things} DgScripts")

            for j in rj:
                vnum = j["HasVnum"]["vnum"]
                dj = j.pop("DgScriptProto")
                dj["key"] = strip_ansi(CircleToEvennia(j.pop("Name", f"Script {vnum}")))
                dj["lines"] = dj.pop("cmdlist", list())

                final = {f"db_{k}": v for k, v in dj.items()}
                final["id"] = vnum

                new_script = DefaultDGScript(**final)
                new_script.save()
                new_script.db.zone = zone

    def load_shops(self):
        zone_ids = DefaultZone.objects.all().values_list("id", flat=True).order_by("id")

        for zid in zone_ids:
            zone = self.zone_ids[zid]
            z_dir = self.zone_paths[zid]
            f_dir = z_dir / "shops.json"

            if not (f_dir.exists() and f_dir.is_file()):
                continue
            rj = read_json_file(f_dir)
            num_things = len(rj)
            self.msg(f"Loading Zone {zid}: {zone.name}, {num_things} Shops")

            for j in rj:
                j["id"] = j.pop("vnum")
                if "type" in j:
                    j["trade_types"] = j.pop("type")
                for t in ("close1", "close2", "open1", "open2"):
                    if t in j:
                        j[f"time_{t}"] = j.pop(t)
                shop = zone.shops.create(**j)

    def load_guilds(self):
        zone_ids = DefaultZone.objects.all().values_list("id", flat=True).order_by("id")

        for zid in zone_ids:
            zone = self.zone_ids[zid]
            z_dir = self.zone_paths[zid]
            f_dir = z_dir / "guilds.json"

            if not (f_dir.exists() and f_dir.is_file()):
                continue
            rj = read_json_file(f_dir)
            num_things = len(rj)
            self.msg(f"Loading Zone {zid}: {zone.name}, {num_things} Guilds")

            for j in rj:
                j["id"] = j.pop("vnum")
                for t in ("open", "close"):
                    if t in j:
                        j[f"time_{t}"] = j.pop(t)
                guild = zone.guilds.create(**j)

    def load_rooms(self):
        zone_ids = DefaultZone.objects.all().values_list("id", flat=True).order_by("id")

        exit_map = defaultdict(dict)
        room_map = dict()

        for zid in zone_ids:
            zone = self.zone_ids[zid]
            z_dir = self.zone_paths[zid]
            rf_dir = z_dir / "rooms.json"
            if not (rf_dir.exists() and rf_dir.is_file()):
                continue
            rj = read_json_file(rf_dir)
            num_rooms = len(rj)
            self.msg(f"Loading Zone {zid}: {zone.name}, {num_rooms} rooms")

            for j in rj:
                vnum = j["vnum"]
                color_name = CircleToEvennia(j.pop("name", f"Room {vnum}"))

                data = dict()
                key = strip_ansi(color_name)

                j["color_name"] = color_name
                if "desc" in j:
                    j["desc"] = CircleToEvennia(j.pop("desc"))

                if "ex_descriptions" in j:
                    j["ex_descriptions"] = [[keyword, CircleToEvennia(desc)] for keyword, desc in j.pop("ex_descriptions")]

                if "global_vars" in j:
                    vars = defaultdict(dict)
                    for varname, context, value in j.pop("global_vars"):
                        vars[context][varname] = value
                    j["dgscript_vars"] = dict(vars)

                exits = j.pop("exits", list())
                if exits:
                    exit_map[zid][vnum] = exits

                data["attributes"] = [[k, v] for k, v in j.items()]

                room, errors = Room.create(key=key, **data)
                if errors:
                    self.msg(errors)
                z_room = zone.rooms.create(id=vnum, obj=room)

                room.db.color_name = color_name

        self.msg(f"Loaded {LegacyRoom.objects.count()} Rooms. Now loading exits...")

        exit_total = 0

        for zid in zone_ids:
            if zid not in exit_map:
                continue
            zone = self.zone_ids[zid]
            self.msg(f"Loading Zone {zid}: {zone.name}, {len(exit_map[zid])} rooms with exits...")
            for rvnum, edata in exit_map[zid].items():
                source = LegacyRoom.objects.get(id=rvnum).obj
                for direction, ed in edata:
                    if not ed:
                        continue
                    e_dir = ExitDir(direction)
                    if (d_vnum := ed.pop("to_room", None)):
                        if (dest := LegacyRoom.objects.filter(id=d_vnum).first()):

                            for t in ("failroom", "totalfailroom"):
                                if t in ed:
                                    if (found := LegacyRoom.objects.filter(id=ed.pop(t)).first()):
                                        ed[t] = found.obj

                            if "general_description" in ed:
                                ed["general_description"] = CircleToEvennia(ed.pop("general_description"))

                            if "key" in ed:
                                ed["key_vnum"] = ed.pop("key")

                            attributes = [[k, v] for k, v in ed.items()]

                            ex, err = Exit.create(e_dir.name.lower(), source, dest.obj, attributes=attributes)
                            if err:
                                self.msg(err)
                            ex.db.direction = int(e_dir)
                            exit_total += 1
                            match e_dir:
                                case ExitDir.NORTH | ExitDir.EAST | ExitDir.SOUTH | ExitDir.WEST | ExitDir.UP | ExitDir.DOWN:
                                    ex.aliases.add(e_dir.name.lower()[0])
                                case ExitDir.INSIDE:
                                    ex.aliases.add("in")
                                case ExitDir.OUTSIDE:
                                    ex.aliases.add("out")
                                case ExitDir.NORTHWEST | ExitDir.NORTHEAST | ExitDir.SOUTHWEST | ExitDir.SOUTHEAST:
                                    low = e_dir.name.lower()
                                    ex.aliases.add(low[0] + low[5])
                                    ex.aliases.add(low[:6])


        self.msg(f"Loaded {exit_total} Exits!")


    def execute(self):

        self.msg("Importing Zones...")
        self.load_zones()
        self.msg(f"Imported {DefaultZone.objects.count()} Zones!")

        self.msg("Importing DgScripts...")
        self.load_dgscripts()
        self.msg(f"Imported {DefaultDGScript.objects.count()} DgScripts!")

        self.msg("Importing Rooms...")
        self.load_rooms()
        self.msg(f"Imported {LegacyRoom.objects.count()} Rooms!")

        self.msg("Importing Shops...")
        self.load_shops()
        self.msg(f"Imported {LegacyShop.objects.count()} Shops!")

        self.msg("Importing Guilds...")
        self.load_guilds()
        self.msg(f"Imported {LegacyGuild.objects.count()} Guilds!")

        self.msg("Importing Items...")
        count = self.load_items()
        self.msg(f"Imported {count} Items!")

        self.msg("Importing Mobiles...")
        count = self.load_mobiles()
        self.msg(f"Imported {count} Mobiles!")

        self.msg("Importing Accounts...")
        count = self.load_accounts()
        self.msg(f"Imported {count} Accounts!")

        self.msg("Importing Player Characters...")
        count = self.load_characters()
        self.msg(f"Imported {count} Player Characters!")

        self.msg("Importing Houses...")
        #count = self.load_houses()
        self.msg(f"Imported {count} Houses!")

        self.proto_file.close()
