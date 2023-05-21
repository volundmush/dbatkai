"""
This accursed module will hold all of the logic necessary for
importing data from the original DBAT into DBAT Kai.

Fuck me, I'm gonna hate writing it.
"""
from pathlib import Path
from collections import defaultdict
import sqlite3
import typing
import traceback
from django.db import IntegrityError, transaction

from .color import CircleToEvennia
from athanor.typing import ExitDir
from evennia.utils.ansi import strip_ansi
from evennia.utils import logger

from typeclasses.scripts import Zone, DgScriptPrototype
from typeclasses.rooms import Room
from typeclasses.exits import Exit
from typeclasses import structures
from evennia.typeclasses.tags import Tag
from evennia import search_tag
from evennia.prototypes.prototypes import save_prototype, search_prototype
from evennia.prototypes.spawner import spawn

gships = [
    {"name": "Falcon", "vnums": [3900, 3901, 3902, 3903, 3904], "hatch_room": 3900, "ship_obj": 3900,
     "location": 408},
    {"name": "Simurgh", "vnums": [3905, 3996, 3997, 3998, 3999], "hatch_room": 3905, "ship_obj": 3905,
     "location": 12002},
    {"name": "Zypher", "vnums": [3906, 3907, 3908, 3909, 3910], "hatch_room": 3906, "ship_obj": 3906,
     "location": 4250},
    {"name": "Valkyrie", "vnums": [3911, 3912, 3913, 3914, 3915], "hatch_room": 3911, "ship_obj": 3911,
     "location": 2323},
    {"name": "Phoenix", "vnums": [3916, 3917, 3918, 3919, 3920], "hatch_room": 3916, "ship_obj": 3916,
     "location": 408},
    {"name": "Merganser", "vnums": [3921, 3922, 3923, 3924, 3925], "hatch_room": 3921, "ship_obj": 3921,
     "location": 2323},
    {"name": "Wraith", "vnums": [3926, 3927, 3928, 3929, 3930], "hatch_room": 3930, "ship_obj": 3930,
     "location": 11626},
    {"name": "Ghost", "vnums": [3931, 3932, 3933, 3934, 3935], "hatch_room": 3935, "ship_obj": 3951,
     "location": 8194},
    {"name": "Wisp", "vnums": [3936, 3937, 3938, 3939, 3940], "hatch_room": 3940, "ship_obj": 3940,
     "location": 12002},
    {"name": "Eagle", "vnums": [3941, 3942, 3943, 3944, 3945], "hatch_room": 3945, "ship_obj": 3945,
     "location": 4250},
    {"name": "Spectral", "vnums": {3946, 3947, 3948, 3949, 3950}, "hatch_room": 3950},
    {"name": "Raven", "vnums": {3951, 3952, 3953, 3954, 3955, 3961}, "hatch_room": 3955},
    {"name": "Marauder", "vnums": {3956, 3957, 3958, 3959, 3960}, "hatch_room": 3960},
    {"name": "Vanir", "vnums": {3962, 3963, 3964, 3965}, "hatch_room": 3965},
    {"name": "Aesir", "vnums": {3966, 3967, 3968, 3969, 3970}, "hatch_room": 3970},
    {"name": "Undine", "vnums": {3971, 3972, 3973, 3974, 3975}, "hatch_room": 3975},
    {"name": "Banshee", "vnums": {3976, 3977, 3978, 3979, 3980}, "hatch_room": 3980},
    {"name": "Hydra", "vnums": {3981, 3982, 3983, 3984, 3985}, "hatch_room": 3985},
    {"name": "Medusa", "vnums": {3986, 3987, 3988, 3989, 3990}, "hatch_room": 3990},
    {"name": "Pegasus", "vnums": {3991, 3992, 3993, 3994, 3995}, "hatch_room": 3995},
    {"name": "Zel 1", "vnums": [5824], "hatch_room": 5824},
    {"name": "Zel 2", "vnums": [5825], "hatch_room": 5825}
]

customs = [
    {"name": "Yun-Yammka", "vnums": [19900, 19901, 19902], "hatch_room": 19901, "ship_obj": 19900},
    {"name": "The Dark Archon", "vnums": [19903, 19912, 19913, 19914], "hatch_room": 19912, "ship_obj": 19916},
    {"name": "The Zafir Krakken", "vnums": [19904, 19905, 19906, 19907], "hatch_room": 19905,
     "ship_obj": 19905},
    {"name": "Crimson Talon", "vnums": [19908, 19909, 19910, 19911], "hatch_room": 19908, "ship_obj": 19910},
    {"name": "Rust Bucket", "vnums": {19915, 19916, 19918, 19930}, "hatch_room": 19915, "ship_obj": 19921},
    {"name": "The Adamant", "vnums": {19917, 19949, 19955, 19956}, "hatch_room": 19949, "ship_obj": 19966},
    {"name": "Vanguard", "vnums": {19919, 19920, 19921, 19922}, "hatch_room": 19949, "ship_obj": 19926},
    {"name": "The Glacial Shadow", "vnums": {19925, 19923, 19924, 19926}, "hatch_room": 19923,
     "ship_obj": 19931},
    {"name": "The Molecular Dynasty", "vnums": {19927, 19928, 19929, 19954}, "hatch_room": 19927,
     "ship_obj": 19936},
    {"name": "Poseidon", "vnums": {19931, 19933, 19932, 19934}, "hatch_room": 19931, "ship_obj": 19941},
    {"name": "Sakana Mirai", "vnums": {19935, 19936, 19937, 19938}, "hatch_room": 19935, "ship_obj": 19946},
    {"name": "Earth Far Freighter Enterjection", "vnums": {19939, 19940, 19941, 19942}, "hatch_room": 19939,
     "ship_obj": 19951},
    {"name": "Soaring Angel", "vnums": {19943, 19944, 19945, 19946}, "hatch_room": 19943, "ship_obj": 19956},
    {"name": "The Grey Wolf", "vnums": {19947, 19948, 19978, 19979}, "hatch_room": 19947, "ship_obj": 19961},
    {"name": "The Event Horizon", "vnums": {19950, 19951, 19980, 19981}, "hatch_room": 19950,
     "ship_obj": 19971},
    {"name": "Fleeting Star", "vnums": {19952, 19953, 19957, 19958}, "hatch_room": 19952, "ship_obj": 19976},
    {"name": "Makenkosappo", "vnums": {19959, 19960, 19961, 19962}, "hatch_room": 19959, "ship_obj": 19981},
    {"name": "The Nightingale", "vnums": {19963, 19964, 19965, 19982}, "hatch_room": 19963, "ship_obj": 19986},
    {"name": "The Honey Bee", "vnums": {19966, 19967, 19968, 19969}, "hatch_room": 19966, "ship_obj": 19991},
    {"name": "The Bloodrose", "vnums": {19970, 19971, 19972, 19973}, "hatch_room": 19970, "ship_obj": 19996},
    {"name": "The Stimato", "vnums": {19974, 19975, 19976, 19977}, "hatch_room": 19974},
    {"name": "The Tatsumaki", "vnums": {15805, 15806, 15807, 15808}, "hatch_room": 15805, "ship_obj": 15805},
    {"name": "Shattered Soul", "vnums": [15800, 15801, 15802, 15803], "hatch_room": 15800}
]


class Importer:

    def __init__(self, caller, path: Path):
        self.caller = caller
        self.path = path
        # Get Sqlite3 going.
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row

    def load_zones(self):
        if Zone.objects.filter_family().count():
            self.msg("Zones already loaded.")
            return

        c = self.conn.cursor()
        c.execute("SELECT * FROM zones ORDER BY id ASC")
        rows = c.fetchall()
        count = len(rows)
        self.msg(f"Loading {count} zones...")

        for i, row in enumerate(rows):
            color_name = CircleToEvennia(row["name"])
            clean_name = strip_ansi(color_name)
            self.msg(f"Importing Zone {row['id']}: {clean_name} ({i + 1}/{count})")
            new_zone, err = Zone.create(f"legacy_zone_{row['id']}")
            if err:
                raise Exception(f"Error creating Zone {row['id']}: {err}")

            new_zone.db.name = color_name
            new_zone.db.min = row["bot"]
            new_zone.db.max = row["top"]

    def zone_for_id(self, vnum: int) -> typing.Optional[Zone]:
        for k, v in Zone.objects.filter_family():
            if vnum >= v.db.min and vnum <= v.db.max:
                return v

    def get_zone(self, zone_id: int):
        return Zone.objects.filter_family(db_key=f"legacy_zone_{zone_id}").first()

    crap_rooms = {157, 3300, 5700, 5826, 5896, 5897, 5898, 5899, 5900, 7700, 15804, 15809, 15882,
                  19000, 19700, 61000, 61500, 62000}

    def load_rooms(self):
        self.msg("Loading Rooms...")

        if Room.objects.filter_family(id=300).first():
            self.msg("Rooms already exist. Skipping.")
            return

        c = self.conn.cursor()

        # First import the Hall of Truth...
        c.execute("SELECT * FROM rooms WHERE id=2")
        row = c.fetchone()
        # Fetch Limbo and update it...
        room = self.get_room(2)
        color_name = CircleToEvennia(row["name"])
        clean_name = strip_ansi(color_name)
        room.key = clean_name
        room.db.short_description = color_name

        if row["look_description"]:
            room.db.desc = CircleToEvennia(row["look_description"])

        # Now import the rest of the rooms...
        # but we want to exclude most of space.
        c.execute(
            "SELECT r.*,st.name AS sector_name FROM rooms AS r LEFT JOIN sector_types AS st ON r.sector_type=st.id WHERE r.id>2 AND (r.id IN (SELECT d.room_id FROM exits as d LEFT JOIN room_flags AS rf ON rf.room_id=d.room_id WHERE d.direction in (4,5,10,11) AND rf.flag_id=27) OR r.id NOT IN (SELECT DISTINCT(room_id) FROM room_flags WHERE flag_id=27)) ORDER BY r.id ASC")
        rows = c.fetchall()
        count = len(rows)
        for i, row in enumerate(rows):
            if row["id"] in self.crap_rooms:
                continue
            color_name = CircleToEvennia(row["name"])
            clean_name = strip_ansi(color_name)
            if i % 100 == 0:
                self.msg(f"Importing Room {i}/{count}: {color_name}")

            room = Room(
                id=row["id"],
                db_key=clean_name,
                db_location=None,
                db_destination=None,
                db_home=None,
                db_typeclass_path=room.path
            )
            room._createdict = {
                "key": clean_name,
                "locks": Room.lockstring.format(id=row["id"])
            }
            room.save()

            if room.id != row["id"]:
                raise Exception(f"Room ID mismatch: ObjectDB {room.id} != source {row['id']}")
            room.db.short_description = color_name

            if row["look_description"]:
                room.db.desc = CircleToEvennia(row["look_description"])
            if (zone := self.get_zone(row["zone_id"])):
                room.db.zone = zone
                zone.db.rooms.add(room)
            else:
                self.msg(f"WARNING: No zone found for Room {row['id']}!")

            # Save these to region_names for later.
            if row["sense_location"] != "Unknown.":
                room.tags.add(category="sense_location", key=row["sense_location"], data=row["sense_location"])

            room.db.sector_name = row["sector_name"]

            c.execute(
                "SELECT rb.name from room_flags AS rf LEFT JOIN room_bits AS rb ON rf.flag_id=rb.id WHERE rf.room_id=?",
                (row['id'],))
            for rf in c.fetchall():
                room.tags.add(category="room_flags", key=rf["name"])

            scripts = []
            c.execute("SELECT * from room_scripts WHERE room_id=?", (row['id'],))
            for script in c.fetchall():
                script_id = script["script_id"]
                if not (
                        dg_script := DgScriptPrototype.objects.filter_family(db_key=f"dg_script_{script_id}").first()):
                    continue
                scripts.append(dg_script.key)
            if scripts:
                room.db.scripts = scripts

    def get_room(self, id: int) -> typing.Optional[Room]:
        return Room.objects.filter_family(id=id).first()

    def load_exits(self):
        self.msg("Loading Rooms...")

        if Exit.objects.filter_family(db_destination__gt=2).count():
            self.msg("Exits already loaded, skipping.")
            return

        c = self.conn.cursor()

        c.execute(
            "SELECT * FROM exits WHERE room_id>1  AND (room_id IN (SELECT d.room_id FROM exits as d LEFT JOIN room_flags AS rf ON rf.room_id=d.room_id WHERE d.direction in (4,5,10,11) AND rf.flag_id=27) OR room_id NOT IN (SELECT DISTINCT(room_id) FROM room_flags WHERE flag_id=27)) ORDER BY id ASC")
        rows = c.fetchall()
        count = len(rows)

        for i, row in enumerate(rows):
            if not (room := self.get_room(row["room_id"])):
                continue
            if i % 1000 == 0:
                self.msg(f"Importing Exit {i}/{count}: {row['id']}")
            destination = self.get_room(row["to_room"])

            e_dir = ExitDir(row["direction"])

            if (gen := row["general_description"]):
                room.db.desc = CircleToEvennia(gen)

            new_exit, err = Exit.create(e_dir.name.lower(), room, destination)
            if err:
                raise Exception(f"Error creating Exit {row['id']}: {err}")
            match e_dir:
                case ExitDir.NORTH | ExitDir.EAST | ExitDir.SOUTH | ExitDir.WEST | ExitDir.UP | ExitDir.DOWN:
                    new_exit.aliases.add(e_dir.name.lower()[0])
                case ExitDir.INSIDE:
                    new_exit.aliases.add("in")
                case ExitDir.OUTSIDE:
                    new_exit.aliases.add("out")
                case ExitDir.NORTHWEST | ExitDir.NORTHEAST | ExitDir.SOUTHWEST | ExitDir.SOUTHEAST:
                    low = e_dir.name.lower()
                    new_exit.aliases.add(low[0] + low[5])
                    new_exit.aliases.add(low[:6])

            if (keywords := row["keyword"]):
                for word in strip_ansi(CircleToEvennia(keywords)).split():
                    new_exit.aliases.add(word.lower())

            for key in ("key", "dclock", "dchide"):
                if row[key]:
                    new_exit.attributes.add(key=key, value=row[key])

            c.execute(
                "SELECT eb.name from exits_info AS ef LEFT JOIN exit_bits AS eb ON ef.flag_id=eb.id WHERE ef.exit_id=?",
                (row['id'],))
            for rf in c.fetchall():
                new_exit.tags.add(category="exit_flags", key=rf["name"])

    def placeholders(self, data) -> str:
        return ', '.join('?' * len(data))

    def relocate(self, room, region, sense=False):
        if region.key == "Ancient Castle" and not sense:
            raise Exception(f"Room {room} is in Ancient Castle!")
        room.move_to(region, quiet=True)

    def load_sense_locations(self):
        self.msg("Loading Sense Locations...")
        if structures.Structure.objects.filter_family(db_key='Ancient Castle').count():
            self.msg("Structures already loaded, skipping.")
            return

        for i, tag in enumerate(Tag.objects.filter(db_category="sense_location")):
            region_name = tag.db_data
            if not (rooms := search_tag(category="sense_location", key=tag.db_key)):
                continue
            self.msg(f"Importing Region {i + 1}: {region_name} - {len(rooms)} rooms.")
            region, err = structures.Region.create(region_name)
            if err:
                raise Exception(f"Error creating Region {region_name}: {err}")
            for room in rooms:
                self.relocate(room, region, sense=True)

        # sanity check...
        if len(structures.Region.objects.filter_family(db_key="Ancient Castle").first().contents) > 300:
            raise Exception("Too many rooms in Ancient Castle!")


    def load_structures(self):
        self.msg("Loading Structures...")
        if structures.Structure.objects.filter_family(db_key='Admin Zone').count():
            self.msg("Structures already loaded, skipping.")
            return

        c = self.conn.cursor()

        def assemble_structure(name, region=None, flag_names=None, typeclass=structures.Planet, orbit=None,
                               ids: set[int] = None, **kwargs):
            self.msg(f"Assembling {name}...")
            planet, err = typeclass.create(name)
            if err:
                raise Exception(f"Error creating {name}: {err}")
            if region:
                self.relocate(planet, region)
            if (orb := self.get_room(orbit)):
                planet.db.orbit = orb
            if kwargs:
                for k, v in kwargs.items():
                    planet.attributes.add(key=k, value=v)
            ids = ids or set()
            if orb:
                ids.add(orb.id)
            flag_names = flag_names or set()

            flag_placeholders = self.placeholders(flag_names)
            id_placeholders = self.placeholders(ids)
            query = f"SELECT DISTINCT(room_id) FROM room_flags as rf LEFT JOIN room_bits AS rb ON rf.flag_id=rb.id LEFT JOIN rooms as r ON r.id=rf.room_id WHERE rb.name IN ({self.placeholders(flag_names)}) OR r.id IN ({self.placeholders(ids)})"

            c.execute(query, tuple(flag_names) + tuple(ids))
            rows = c.fetchall()
            self.msg(f"Relocating {len(rows)} rooms to {planet}...")
            for rows in rows:
                if not (room := self.get_room(rows["room_id"])):
                    continue
                if room.location:
                    if not room.location.location:
                        self.relocate(room.location, planet)
                else:
                    self.relocate(room, planet)
            return planet

        admin_zone = assemble_structure("Admin Zone", typeclass=structures.Existence)
        mud_school = assemble_structure("MUD School", typeclass=structures.Existence, ids=set(range(100, 155)))

        multiverse = assemble_structure("The Multiverse", typeclass=structures.Existence)
        xenoverse = assemble_structure("The Xenoverse", typeclass=structures.Existence)

        universe_7 = assemble_structure("Universe 7", typeclass=structures.Universe, region=multiverse)
        mortal_plane = assemble_structure("Mortal Plane", typeclass=structures.Dimension, region=universe_7)
        celestial_plane = assemble_structure("Celestial Plane", typeclass=structures.Dimension, region=universe_7)

        #space_ids = {row['id'] for row in c.execute("SELECT id FROM rooms WHERE clean_name LIKE '%Depths of Space%'").fetchall()}
        #space_ids.add(65199)
        space = assemble_structure("Depths of Space", typeclass=structures.Space, region=mortal_plane)

        planet_earth = assemble_structure("Earth", region=mortal_plane, flag_names={"EARTH"}, orbit=50,
                                          ids={19565, 162, 50}, moon=True, ether_stream=True)

        planet_vegeta = assemble_structure("Vegeta", region=mortal_plane, flag_names={"VEGETA"}, orbit=53, ids=None,
                                           moon=True, gravity=10)

        planet_frigid = assemble_structure("Frigid", region=mortal_plane, flag_names={"FRIGID"}, orbit=51, ids=None,
                                           moon=True)

        planet_konack = assemble_structure("Konack", region=mortal_plane, flag_names={"KONACK"}, orbit=52, ids={19312})
        if (battlefields := structures.Structure.objects.filter_family(db_key='Battlefields').first()):
            battlefields.move_to(planet_konack, quiet=True)

        planet_namek = assemble_structure("Namek", region=mortal_plane, flag_names={"NAMEK"}, orbit=54)

        planet_aether = assemble_structure("Aether", region=mortal_plane, flag_names={"AETHER"}, orbit=55, moon=True,
                                           ether_stream=True)

        planet_yardrat = assemble_structure("Yardrat", region=mortal_plane, flag_names={"YARDRAT"}, orbit=56)

        neo_nirvana = assemble_structure("Neo Nirvana", region=planet_yardrat, flag_names={"NEO"},
                                         typeclass=structures.Region)

        planet_kanassa = assemble_structure("Kanassa", region=mortal_plane, flag_names={"KANASSA"}, orbit=58,
                                            ids={7649})

        planet_arlia = assemble_structure("Arlia", region=mortal_plane, flag_names={"ARLIA"}, orbit=59, ids={7650})

        planet_cerria = assemble_structure("Cerria", region=mortal_plane, flag_names={"CERRIA"}, orbit=198)

        planet_zenith = assemble_structure("Zenith", region=mortal_plane, flag_names={"ZENITH"}, orbit=57,
                                           typeclass=structures.Moon, ids=None)

        for place in structures.Structure.objects.filter_family(db_key__in=("Ancient Castle", "Utatlan City", "Zenith Jungle")):
            print(f"FOUND A PLACE: {place.db_key}")
            place.move_to(planet_zenith, quiet=True)

        underground_cavern = assemble_structure("Underground Cavern", region=planet_zenith,
                                                ids=set(range(62900, 63000)),
                                                typeclass=structures.Region)

        hbtc = assemble_structure("Hyperbolic Time Chamber", region=universe_7, typeclass=structures.Dimension,
                                  ids=set(range(64000, 64098)))

        black_omen_ids_set = {row['id'] for row in
                              c.execute("SELECT id FROM rooms WHERE clean_name LIKE '%Black Omen%'").fetchall()}
        black_omen = assemble_structure("The Black Omen", region=space, typeclass=structures.Region,
                                        ids=black_omen_ids_set)

        northran = assemble_structure("Northran", region=xenoverse, ids=set(range(17900, 18000)),
                                      typeclass=structures.Dimension)

        celestial_corp_ids = {row['id'] for row in
                              c.execute("SELECT id FROM rooms WHERE clean_name LIKE '%Celestial Corp%'").fetchall()}
        celestial_corp_ids.update(set(range(16305, 16399)))
        celestial_corp = assemble_structure("Celestial Corp", region=space, ids=celestial_corp_ids,
                                            typeclass=structures.SpaceStation)

        green_nebula_mall_ids = {row['id'] for row in
                                 c.execute(
                                     "SELECT id FROM rooms WHERE clean_name LIKE '%Green Nebula Mall%'").fetchall()}
        green_nebula_mall_ids.update(set(range(17264, 17277)))
        green_nebula_mall = assemble_structure("Green Nebula Mall", region=space, ids=green_nebula_mall_ids,
                                               typeclass=structures.SpaceStation)

        cooler_ship_ids = {row['id'] for row in
                           c.execute(
                               '''SELECT id, clean_name FROM rooms WHERE clean_name LIKE "%Cooler's Ship%"''').fetchall()}
        cooler_ship = assemble_structure("Cooler's Ship", region=space, ids=cooler_ship_ids,
                                         typeclass=structures.SpaceShip)

        alpharis_ids = {row['id'] for row in
                        c.execute('''SELECT id FROM rooms WHERE clean_name LIKE "%Alpharis%"''').fetchall()}
        alpharis = assemble_structure("Alpharis", region=space, ids=alpharis_ids, typeclass=structures.SpaceStation)

        dead_zone_ids = {row['id'] for row in
                         c.execute('''SELECT id FROM rooms WHERE clean_name LIKE "%Dead Zone%"''').fetchall()}
        dead_zone = assemble_structure("Dead Zone", region=universe_7, ids=dead_zone_ids,
                                       typeclass=structures.Dimension)

        blasted_asteroid_ids = {row['id'] for row in c.execute(
            '''SELECT id FROM rooms WHERE clean_name LIKE "%Blasted Asteroid%"''').fetchall()}
        blasted_asteroid = assemble_structure("Blasted Asteroid", region=space, ids=blasted_asteroid_ids,
                                              typeclass=structures.Asteroid)

        lister_ids = {row['id'] for row in
                      c.execute('''SELECT id FROM rooms WHERE clean_name LIKE "%Lister's Restaurant%"''').fetchall()}
        lister_restaurant = assemble_structure("Lister's Restaurant", region=xenoverse, ids=lister_ids,
                                               typeclass=structures.Region)

        shooting_star_casino_ids = {row['id'] for row in c.execute(
            '''SELECT id FROM rooms WHERE clean_name LIKE "%Shooting Star Casino%"''').fetchall()}
        shooting_star_casino_ids.update(set(range(18500, 18580)))
        shooting_star_casino = assemble_structure("Shooting Star Casino", region=xenoverse,
                                                  ids=shooting_star_casino_ids, typeclass=structures.Region)

        the_outpost_ids = {row['id'] for row in
                           c.execute('''SELECT id FROM rooms WHERE clean_name LIKE "%The Outpost%"''').fetchall()}
        the_outpost = assemble_structure("The Outpost", region=celestial_plane, ids=the_outpost_ids,
                                         typeclass=structures.Region)

        king_yemma_domain_ids = set(range(6000, 6031))
        king_yemma_domain_ids.remove(6017)
        king_yemma_domain = assemble_structure("King Yemma's Domain", region=celestial_plane,
                                               ids=king_yemma_domain_ids, typeclass=structures.Region)

        snake_way_ids = set(range(6031, 6100))
        snake_way_ids.add(6017)
        snake_way = assemble_structure("Snake Way", region=celestial_plane, ids=snake_way_ids)

        king_kai_planet_ids = set(range(6100, 6139))
        king_kai_planet = assemble_structure("North Kai's Planet", region=celestial_plane, ids=king_kai_planet_ids,
                                             typeclass=structures.Planet)

        serpent_castle_ids = set(range(6100, 6167))
        serpent_castle = assemble_structure("Serpent Castle", region=snake_way, ids=serpent_castle_ids)

        grand_kai_planet_ids = set(range(6800, 6961))
        grand_kai_planet = assemble_structure("Grand Kai's Planet", region=celestial_plane, ids=grand_kai_planet_ids,
                                              typeclass=structures.Planet)

        maze_of_echoes_ids = set(range(7100, 7200))
        maze_of_echoes = assemble_structure("Maze of Echoes", region=celestial_plane, ids=maze_of_echoes_ids,
                                            typeclass=structures.Region)

        dark_catacomb_ids = set(range(7200, 7245))
        dark_catacomb = assemble_structure("Dark Catacomb", region=maze_of_echoes, ids=dark_catacomb_ids,
                                           typeclass=structures.Region)

        twilight_cavern_ids = set(range(7300, 7500))
        twilight_cavern = assemble_structure("Twilight Cavern", region=celestial_plane, ids=twilight_cavern_ids,
                                             typeclass=structures.Region)

        hell = assemble_structure("Hell", region=celestial_plane, typeclass=structures.Region)

        hell_fields_ids = set(range(6200, 6300))
        hell_fields = assemble_structure("Hell Fields", region=hell, ids=hell_fields_ids, typeclass=structures.Region)

        hell_sands_of_time_ids = set(range(6300, 6349))
        hell_sands_of_time = assemble_structure("Sands of Time", region=hell, ids=hell_sands_of_time_ids,
                                                typeclass=structures.Region)

        hell_chaotic_spiral_ids = set(range(6349, 6400))
        hell_chaotic_spiral = assemble_structure("Chaotic Spiral", region=hell, ids=hell_chaotic_spiral_ids,
                                                 typeclass=structures.Region)

        hell_hellfire_city_ids = set(range(6400, 6530))
        hell_hellfire_city_ids.update({6568, 6569, 6600, 6699})
        hell_hellfire_city = assemble_structure("Hellfire City", region=hell, ids=hell_hellfire_city_ids,
                                                typeclass=structures.Region)

        flaming_bag_dojo_ids = set(range(6530, 6568))
        # how the hell did Copilot know it stopped at 6568? SERIOUSLY HOW
        flaming_bag_dojo = assemble_structure("Flaming Bag Dojo", region=hell_hellfire_city, ids=flaming_bag_dojo_ids,
                                              typeclass=structures.Region)

        entrail_graveyard_ids = set(range(6601, 6689))
        entrail_graveyard = assemble_structure("Entrail Graveyard", region=hell_hellfire_city,
                                               ids=entrail_graveyard_ids,
                                               typeclass=structures.Region)

        planet_sihnon_ids = set(range(3600, 3700))
        planet_sihnon = assemble_structure("Planet Sihnon", region=space, ids=planet_sihnon_ids,
                                           typeclass=structures.Planet)

        majinton_ids = set(range(3700, 3797))
        majinton = assemble_structure("Majinton", region=planet_sihnon, ids=majinton_ids,
                                      typeclass=structures.Dimension)

        wisdom_tower_ids = set(range(39600, 9667))
        wisdom_tower = assemble_structure("Wisdom Tower", region=planet_namek, ids=wisdom_tower_ids,
                                          typeclass=structures.Region)

        machiavilla_ids = set(range(12743, 12798))
        machiavilla = assemble_structure("Machiavilla", region=planet_konack, ids=machiavilla_ids,
                                         typeclass=structures.Region)

        monastery_of_balance_ids = set(range(9537, 9366))
        monastery_of_balance = assemble_structure("Monastery of Balance", region=planet_konack,
                                                  ids=monastery_of_balance_ids,
                                                  typeclass=structures.Region)

        future_school_ids = set(range(15938, 16000))
        future_school = assemble_structure("Future School", region=xenoverse, ids=future_school_ids,
                                           typeclass=structures.Region)

        udf_headquarters_ids = set(range(18000, 18059))
        udf_headquarters = assemble_structure("UDF Headquarters", region=space, ids=udf_headquarters_ids,
                                              typeclass=structures.SpaceStation)

        the_haven_spire_ids = set(range(18300, 18341))
        the_haven_spire = assemble_structure("The Haven Spire", region=space, ids=the_haven_spire_ids,
                                             typeclass=structures.SpaceStation)

        kame_no_itto_ids = set(range(18400, 18460))
        kame_no_itto = assemble_structure("Kame no Itto", region=space, ids=kame_no_itto_ids,
                                          typeclass=structures.SpaceStation)

        shattered_galaxy_ids = set(range(64300, 64399))
        shattered_galaxy = assemble_structure("Shattered Galaxy", region=space, ids=shattered_galaxy_ids,
                                              typeclass=structures.Region)

        war_zone = assemble_structure("War Zone", region=xenoverse, typeclass=structures.Region,
                                      ids=set(range(17700, 17703)))

        corridor_of_light = assemble_structure("Corridor of Light", region=war_zone, typeclass=structures.Region,
                                               ids=set(range(17703, 17723)))

        corridor_of_darkness = assemble_structure("Corridor of Darkness", region=war_zone, typeclass=structures.Region,
                                                  ids=set(range(17723, 17743)))

        south_ocean_island_ids = set(range(6700, 6758))
        south_ocean_island = assemble_structure("South Ocean Island", region=planet_earth, ids=south_ocean_island_ids,
                                                typeclass=structures.Region)

        haunted_house_ids = set(range(18600, 18693))
        haunted_house = assemble_structure("Haunted House", region=xenoverse, ids=haunted_house_ids,
                                           typeclass=structures.Region)

        random_occurence_wtf_ids = set(range(18700, 18776))
        random_occurence_wtf = assemble_structure("Random Occurence, WTF?", region=xenoverse,
                                                  ids=random_occurence_wtf_ids,
                                                  typeclass=structures.Region)

        galaxy_strongest_tournament_ids = {17875, 17876, 17877, 17893, 17891}
        galaxy_strongest_tournament = assemble_structure("Galaxy's Strongest Tournament", region=space,
                                                         ids=galaxy_strongest_tournament_ids,
                                                         typeclass=structures.Region)

        arena_water_ids = set(range(17800, 17825))
        arena_water = assemble_structure("Arena - Water", region=galaxy_strongest_tournament, ids=arena_water_ids,
                                         typeclass=structures.Region)

        arena_the_ring_ids = set(range(17825, 17850))
        arena_the_ring = assemble_structure("Arena - The Ring", region=galaxy_strongest_tournament,
                                            ids=arena_the_ring_ids,
                                            typeclass=structures.Region)

        arena_in_the_sky_ids = set(range(17850, 17875))
        arena_in_the_sky = assemble_structure("Arena - In The Sky", region=galaxy_strongest_tournament,
                                              ids=arena_in_the_sky_ids,
                                              typeclass=structures.Region)

        arena_great_hall_ids = set(range(17878, 17891))
        arena_great_hall = assemble_structure("Arena - Great Hall", region=galaxy_strongest_tournament,
                                              ids=arena_great_hall_ids,
                                              typeclass=structures.Region)

        def crunch_ship(ship_data: dict, tag_category: str, tag_name: str):
            if "ship_obj" in ship_data and (ship_proto := search_prototype(f"legacy_item_{ship_data.get('ship_obj')}")):
                ship_obj = spawn(ship_proto[0])[0]
            else:
                ship_obj, err = structures.SpaceShip.create(ship_data.get("name"))
                if err:
                    raise Exception(err)
                for d in ("room_description", "short_description", "look_description"):
                    ship_obj.attributes.add(key=d, value=ship_data.get("name"))
            ship_obj.tags.add(category=tag_category, key=tag_name)

            for vnum in ship_data.get("vnums", list()):
                if (room := self.get_room(vnum)):
                    self.relocate(room, ship_obj)
                    if vnum == ship_data.get("hatch_room", None):
                        room.tags.add(category="room_flags", key="hatch")
                        ship_obj.destination = room

            return ship_obj

        for ship in gships:
            crunch_ship(ship, "spaceships", "public_transport")

        for ship in customs:
            crunch_ship(ship, "spaceships", "player_ship")

        # saiyan pods...
        for vnum in range(46000, 46055):
            result = c.execute(
                "SELECT value FROM object_values AS ov LEFT JOIN item_prototypes_view AS ipv ON ipv.id = ov.object_id WHERE ipv.vnum= ?",
                (vnum,)).fetchone()
            ship_data = {"vnums": [result['value']], "ship_obj": vnum, "hatch_room": vnum}
            result = c.execute("SELECT name FROM item_prototypes_view WHERE vnum= ?", (vnum,)).fetchone()
            ship_data["name"] = result['name']
            s = crunch_ship(ship_data, "spaceships", "player_ship")
            s.tags.add(category="spaceships", key="saiyan_pod")

        # EDI Xeno-Fighter Mk. II
        for vnum in range(46100, 46150):
            result = c.execute(
                "SELECT value FROM object_values AS ov LEFT JOIN item_prototypes_view AS ipv ON ipv.id = ov.object_id WHERE ipv.vnum= ?",
                (vnum,)).fetchone()
            ship_data = {"vnums": [result['value']], "ship_obj": vnum, "hatch_room": vnum}
            result = c.execute("SELECT name FROM item_prototypes_view WHERE vnum= ?", (vnum,)).fetchone()
            ship_data["name"] = result['name']
            s = crunch_ship(ship_data, "spaceships", "player_ship")
            s.tags.add(category="spaceships", key="xenofighter")

        # small player houses
        for i, v in enumerate(range(18800, 18900, 4)):
            house = assemble_structure(f"Small House {i + 1}", region=None, ids=set(range(v, v + 4)),
                                       typeclass=structures.PlayerHouse)
            house.tags.add(category="player_houses", key="small_house")

        # deluxe player houses
        for i, v in enumerate(range(18900, 19000, 5)):
            house = assemble_structure(f"Deluxe House {i + 1}", region=None, ids=set(range(v, v + 5)),
                                       typeclass=structures.PlayerHouse)
            house.tags.add(category="player_houses", key="deluxe_house")

        # excellent player houses
        for i, v in enumerate(range(19000, 19100, 5)):
            house = assemble_structure(f"Excellent House {i + 1}", region=None, ids=set(range(v, v + 5)),
                                       typeclass=structures.PlayerHouse)
            house.tags.add(category="player_houses", key="excellent_house")

        unknown_house = assemble_structure("Unknown House", region=None,
                                           ids={19009, 19010, 19011, 19012, 19013, 19014, 19015, 19016, 19017, 19018,
                                                19019, 19020, 19021, 19022, 19023}, typeclass=structures.PlayerHouse)
        unknown_house.tags.add(category="player_houses", key="custom_house")

        mountaintop_fortress = assemble_structure("Mountaintop Fortress", region=None,
                                                  ids={19025, 19026, 19027, 19028, 19029, 19030, 19031, 19032,
                                                       19033, 19034, 19035, 19036, 19037, 19038},
                                                  typeclass=structures.PlayerHouse)
        mountaintop_fortress.tags.add(category="player_houses", key="custom_house")

        for i, v in enumerate(range(19800, 19900)):
            pocket_dimension = assemble_structure(f"Personal Pocket Dimension {i + 1}", region=None, ids={v},
                                                  typeclass=structures.PocketDimension)
            pocket_dimension.tags.add(category="player_houses", key="pocket_dimension")

        exit_count = -1
        while True:
            if (exits_found := Exit.objects.filter_family(db_destination__db_location__isnull=False, db_location__db_location=None)):
                if len(exits_found) == exit_count:
                    break
                exit_count = len(exits_found)
                self.msg(f"Relocating {len(exits_found)} rooms...")
                for ex in exits_found:
                    self.relocate(ex.location, ex.destination.location)
            else:
                break

        if (unknowns := Room.objects.filter_family(db_location=None)):
            self.msg("Binding unknown rooms to an unknown region...")
            unknown_region = assemble_structure("Unknown Region", typeclass=structures.Region, region=xenoverse)
            for room in unknowns:
                self.relocate(room, unknown_region)

    def load_dgscripts(self):
        if DgScriptPrototype.objects.filter_family().count():
            self.msg("DGScripts already loaded.")
            return
        c = self.conn.cursor()
        trig_types = {}
        for id, table_name in ((0, "trig_types"), (1, "otrig_types"), (2, "wtrig_types")):
            trig_types[id] = c.execute(f"SELECT * FROM {table_name}").fetchall()

        c.execute("SELECT * FROM scripts")
        rows = c.fetchall()
        count = len(rows)
        self.msg(f"Loading {count} DGScripts...")

        for i, row in enumerate(rows):
            if i % 100 == 0:
                self.msg(f"Loading DGScript {i} of {count}...")
            script, err = DgScriptPrototype.create(f"dg_script_{row['id']}", autostart=False)
            if err:
                raise Exception(f"Error loading DGScript {row['id']}: {err}")
            attach_type = row['attach_type']
            match attach_type:
                case 0:
                    script.db.script_type = "npc"
                case 1:
                    script.db.script_type = "item"
                case 2:
                    script.db.script_type = "room"
                case _:
                    raise Exception(f"Unknown attach_type {attach_type} for DGScript {row['id']}")

            trigger_type = row["trigger_type"]
            type_tuples = ((d['id'], d['name']) for d in trig_types[attach_type])
            for i, (bit_index, bit_name) in enumerate(type_tuples):
                if trigger_type & (1 << bit_index):
                    script.tags.add(category="trigger_type", key=bit_name)

            for field in ("name", "script_body", "arglist"):
                script.attributes.add(key=field, value=row[field])
            if (zone := self.get_zone(row['zone_id'])):
                script.db.zone = zone

    wears = {0: "take", 1: "finger", 2: "neck", 3: "body", 4: "head", 5: "legs", 6: "feet", 7: "hands", 8: "arms",
             9: "shield", 10: "about", 11: "waist", 12: "wrist", 13: "wield", 14: "hold", 15: "back", 16: "ear",
             17: "shoulders", 18: "eyes"}

    def load_item_prototypes(self):
        if search_prototype("legacy_item_3"):
            self.msg("Item prototypes already loaded.")
            return
        c = self.conn.cursor()
        c.execute(
            "SELECT o.*,it.name as type_name FROM item_prototypes_view AS o LEFT JOIN item_types AS it ON o.type_flag = it.id")
        rows = c.fetchall()
        count = len(rows)
        self.msg(f"Loading {count} item prototypes...")

        for i, row in enumerate(rows):
            proto = {
                "prototype_key": f"legacy_item_{row['vnum']}",
                "key": strip_ansi(CircleToEvennia(row['name'])),
                "vnum": row['vnum'],
            }
            if i % 100 == 0:
                self.msg(f"Loading item prototype {i} of {count}...")
            for thing in ('look_description', 'room_description', 'short_description'):
                if row[thing]:
                    proto[thing] = CircleToEvennia(row[thing])

            for thing in ('level', 'weight', 'cost', 'cost_per_day', 'size'):
                if row[thing]:
                    proto[thing] = row[thing]

            c.execute("SELECT * from object_extra_desc WHERE object_id=?", (row['id'],))
            if extra_descs := c.fetchall():
                extra_d = []
                for extra_desc in extra_descs:
                    extra_d.append({
                        "keywords": extra_desc['keyword'],
                        "description": CircleToEvennia(extra_desc['description'])
                    })
                proto["extra_descriptions"] = extra_d

            c.execute("SELECT * from object_scripts WHERE object_id=?", (row['id'],))
            if scripts := c.fetchall():
                proto_scripts = []
                for script in scripts:
                    script_id = script["script_id"]
                    if not (
                    dg_script := DgScriptPrototype.objects.filter_family(db_key=f"dg_script_{script_id}").first()):
                        continue
                    proto_scripts.append(dg_script.key)
                if proto_scripts:
                    proto["dg_scripts"] = proto_scripts

            match row['type_name']:
                case "VEHICLE":
                    proto["typeclass"] = "typeclasses.structures.SpaceShip"
                case "PORTAL":
                    proto["typeclass"] = "typeclasses.objects.Portal"
                case _:
                    proto["typeclass"] = "typeclasses.objects.Item"

            tags = [("item_type", row['type_name'], None)]

            c.execute(
                "SELECT eb.name from object_extra_flags AS oef LEFT JOIN extra_bits AS eb ON oef.extra_flag_id=eb.id WHERE oef.object_id=?",
                (row['id'],))
            if extra_flags := c.fetchall():
                tags.extend([(ef['name'], 'extra_flags', None) for ef in extra_flags])

            c.execute(
                "SELECT ab.name from object_affected_flags AS oaf LEFT JOIN affected_bits AS ab ON oaf.affected_flag_id=ab.id WHERE oaf.object_id=?",
                (row['id'],))
            if affected_flags := c.fetchall():
                tags.extend([(ef['name'], 'affected_flags', None) for ef in affected_flags])

            c.execute("SELECT position,value FROM object_values WHERE object_id=?", (row['id'],))
            values = {v['position']: v['value'] for v in c.fetchall()}
            if values:
                proto["item_values"] = values

            c.execute("SELECT wear_flag_id from object_wear_flags WHERE object_id=?", (row['id'],))
            if wear_flags := c.fetchall():
                tags.extend([(self.wears.get(ef['wear_flag_id']), 'wear_flags', None) for ef in wear_flags])

            proto["tags"] = tags

            c.execute(
                "SELECT oe.object_id,at.name,oe.specific,oe.modifier from object_affects AS oe LEFT JOIN apply_types AS at ON oe.location=at.id WHERE oe.object_id=?",
                (row['id'],))
            if effect_data := c.fetchall():
                component_data = []
                for effect in effect_data:
                    match effect['name']:
                        case "WIS":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "wisdom", "value": effect['modifier']}))
                        case "INT":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "intelligence", "value": effect['modifier']}))
                        case "STR":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "strength", "value": effect['modifier']}))
                        case "AGL":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "agility", "value": effect['modifier']}))
                        case "CON":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "constitution", "value": effect['modifier']}))
                        case "SPD":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "speed", "value": effect['modifier']}))
                        case "ALL_STATS":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "all_stats", "value": effect['modifier']}))
                        case "ARMOR":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "armor", "value": effect['modifier']}))
                        case "AUTO-TRAIN SKILL":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "autotrain", "value": effect['modifier']}))
                        case "DAMAGE":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "damage", "value": effect['modifier']}))
                        case "EXP":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "exp", "value": effect['modifier']}))
                        case "FISHBONUS":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "fishbonus", "value": effect['modifier']}))
                        case "LEVEL":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "level", "value": effect['modifier']}))
                        case "LIFEFORCE MAX":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "lifeforce_max", "value": effect['modifier']}))
                        case "MAXKI":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "ki_max", "value": effect['modifier']}))
                        case "MAXPL":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "pl_max", "value": effect['modifier']}))
                        case "MAXST":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "st_max", "value": effect['modifier']}))
                        case "REGEN RATE":
                            component_data.append(
                                ("ModifierStatic", {"modifier": "regen_rate", "value": effect['modifier']}))
                        case "SKILL":
                            component_data.append(
                                ("ModifierStatic",
                                 {"modifier": f"skill_{effect['specific']}", "value": effect['modifier']}))
                        case _:
                            pass
                if component_data:
                    proto["effect"] = {"component_data": component_data}

            save_prototype(proto)

    def load_npc_prototypes(self):
        if search_prototype("legacy_npc_1125"):
            self.msg("NPC prototypes already loaded.")
            return
        c = self.conn.cursor()
        c.execute(
            "SELECT * FROM npc_prototypes_view")
        rows = c.fetchall()
        count = len(rows)
        self.msg(f"Loading {count} item prototypes...")

        for i, row in enumerate(rows):
            if i % 100 == 0:
                self.msg(f"Loading {i} of {count} item prototypes...")
            proto = {
                "prototype_key": f"legacy_npc_{row['vnum']}",
                "key": strip_ansi(CircleToEvennia(row['name'])),
                "typeclass": "typeclasses.characters.NonPlayerCharacter",
                "vnum": row['vnum'],
            }
            for thing in ('look_description', 'room_description', 'short_description'):
                if row[thing]:
                    proto[thing] = CircleToEvennia(row[thing])

            for thing in ('level', 'level_adj', 'race_level', 'level_adj', 'alignment', 'armor', 'gold', 'damage_mod',
                          'basepl', 'baseki', 'basest', 'str', 'intel', 'wis', 'dex', 'con', 'cha', 'attack_type',
                          'default_pos', 'damnodice', 'damsizedice'):
                if row[thing]:
                    proto[thing] = row[thing]

            c.execute("SELECT * from character_scripts WHERE character_id=?", (row['id'],))
            if scripts := c.fetchall():
                proto_scripts = []
                for script in scripts:
                    script_id = script["script_id"]
                    if not (
                    dg_script := DgScriptPrototype.objects.filter_family(db_key=f"dg_script_{script_id}").first()):
                        continue
                    proto_scripts.append(dg_script.key)
                if proto_scripts:
                    proto["dg_scripts"] = proto_scripts

            tags = []

            c.execute(
                "SELECT ab.name from character_act_bits AS cab LEFT JOIN action_bits AS ab ON cab.act_bit=ab.id WHERE cab.character_id=?",
                (row['id'],))
            if mob_flags := c.fetchall():
                tags.extend([(ef['name'], 'mob_flags', None) for ef in mob_flags])

            c.execute(
                "SELECT ab.name from character_affected_bits AS cab LEFT JOIN affected_bits AS ab ON cab.affected_bit=ab.id WHERE cab.character_id=?",
                (row['id'],))
            if affected_flags := c.fetchall():
                tags.extend([(ef['name'], 'affected_flags', None) for ef in affected_flags])

            if tags:
                proto["tags"] = tags

            save_prototype(proto)

    def execute(self):
        try:
            for routine in (self.load_zones, self.load_dgscripts, self.load_item_prototypes,
                            self.load_npc_prototypes, self.load_rooms, self.load_exits,
                            self.load_sense_locations, self.load_structures):
                with transaction.atomic():
                    routine()
        except Exception as err:
            tb_str = traceback.format_exception(err)
            full_traceback_str = "".join(tb_str)
            print(f"IMPORT ERROR:\n{full_traceback_str}")
            logger.log_err(full_traceback_str)

    def run(self):
        pass

    def msg(self, text: str):
        logger.log_info(text)
        print(text)


def run_import():
    path = Path("C:\\Users\\basti\\CLionProjects\\dbat\\lib\\dbat.sqlite3")
    importer = Importer(None, path)
    importer.execute()
