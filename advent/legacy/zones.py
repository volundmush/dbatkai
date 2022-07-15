from evennia.typeclasses.models import TypeclassBase
from evennia.prototypes.prototypes import search_prototype
from evennia.prototypes.spawner import spawn
from random import randint
from athanor.systems import sleep_for
from advent.legacy.models import LegacyRoom
from evennia import search_tag
from advent.legacy.models import ZoneDB


class DefaultZone(ZoneDB, metaclass=TypeclassBase):

    def at_first_save(self):
        pass

    async def reset(self):
        #print(f"Resetting Zone: {self.id}: {self.key}")

        last_loaded = None
        last_cmd = False
        # fully load all commands in one query.
        all_commands = list(self.commands.all().order_by("line"))

        for cmd in all_commands:
            await sleep_for(0.05)
            #print(f"Processing Line {cmd.line}: {cmd.command} {cmd.arg1} {cmd.arg2} {cmd.arg3} {cmd.arg4} {cmd.arg5}")

            if cmd.if_flag:
                if not (last_cmd or last_loaded):
                    continue
            else:
                last_loaded = None

            try:
                match cmd.command:
                    # Comment
                    case "*":
                        last_cmd = False
                        continue

                    # Load a Mobile.
                    case "M":
                        if not (room := LegacyRoom.objects.filter(id=cmd.arg3).first()):
                            last_cmd = False
                            last_loaded = None
                            continue

                        proto_key = f"legacy_mobile_{cmd.arg1}"
                        proto_list = search_prototype(key=proto_key, require_single=True)
                        proto = proto_list[0]

                        # Roll the chance dice. if arg5 is 0 this will always succeed.
                        if not randint(1, 100) >= cmd.arg5:
                            last_cmd = False
                            last_loaded = None
                            continue

                        # arg4 is the max amount of mobiles that can have loaded with this room as a home.
                        if cmd.arg4 > 0:
                            total_amount = search_tag(proto_key, category="from_prototype").filter(db_home=room.obj, db_location__legacy_room__zone__isnull=False).count()
                            if total_amount >= cmd.arg4:
                                continue

                        #print(f"For Room {room.id}: Loading Mobile {cmd.arg1}: {proto['key']}")
                        for mob in spawn(proto):
                            mob.home = room.obj
                            mob.move_to(room.obj, quiet=True)

                            last_loaded = mob
                            last_cmd = True

                    # Load an Object / Item.
                    case "O":
                        if not (room := LegacyRoom.objects.filter(id=cmd.arg3).first()):
                            last_cmd = False
                            last_loaded = None
                            continue

                        proto_key = f"legacy_item_{cmd.arg1}"
                        proto_list = search_prototype(key=proto_key, require_single=True)
                        proto = proto_list[0]

                        # Roll the chance dice. if arg5 is 0 this will always succeed.
                        if not randint(1, 100) >= cmd.arg5:
                            last_cmd = False
                            last_loaded = None
                            continue

                        # arg4 is the max amount of mobiles that can be in this room.
                        if cmd.arg4 > 0:
                            total_amount = search_tag(proto_key, category="from_prototype").filter(db_home=room.obj, db_location=room.obj).count()
                            if total_amount >= cmd.arg4:
                                continue

                        #print(f"For Room {room.id}: Loading Item {cmd.arg1}: {proto['key']}")
                        for item in spawn(proto):
                            item.home = room.obj
                            item.move_to(room.obj, quiet=True)

                            last_loaded = item
                            last_cmd = True

                    # Create an Item and add it to last loaded object's Inventory.
                    case "G" | "P":
                        if not last_loaded:
                            continue

                        proto_list = search_prototype(key=f"legacy_item_{cmd.arg1}", require_single=True)
                        proto = proto_list[0]

                        # Roll the chance dice. if arg5 is 0 this will always succeed.
                        if not randint(1, 100) >= cmd.arg5:
                            last_cmd = False
                            last_loaded = None
                            continue

                        #print(f"For the new {last_loaded.key}: Giving Item {cmd.arg1}: {proto['key']}")
                        for item in spawn(proto):
                            item.move_to(last_loaded, quiet=True)
                            last_cmd = True

                    # Create an Item and equip it to the last loaded object's equipment.
                    case "E":
                        if not last_loaded:
                            continue

                        proto_list = search_prototype(key=f"legacy_item_{cmd.arg1}", require_single=True)
                        proto = proto_list[0]

                        # Roll the chance dice. if arg5 is 0 this will always succeed.
                        if not randint(1, 100) >= cmd.arg5:
                            last_cmd = False
                            last_loaded = None
                            continue

                        #print(f"For the new {last_loaded.key}: Equipping Item {cmd.arg1}: {proto['key']} to slot {cmd.arg3}")
                        for item in spawn(proto):
                            item.move_to(last_loaded, quiet=True)
                            last_loaded.equipment.equip(cmd.arg3, item)
                            last_cmd = True

                    # Set State of door.
                    case "D":
                        pass

                    # Assign a Trigger.
                    case "T":
                        if not last_loaded:
                            continue
                        #print(f"For the new {last_loaded.key}: Assigning Trigger {cmd.arg2}")
                        last_loaded.dgscripts.attach(cmd.arg2)

                    # Assign a variable.
                    case "V":
                        if not last_loaded:
                            continue
                        #print(f"For the new {last_loaded.key}: Setting Global var {cmd.arg3} {cmd.sarg1} to: {cmd.sarg2}")
                        last_loaded.dgscripts.vars[cmd.arg3][cmd.sarg1] = cmd.sarg2

            except KeyError as err:
                last_cmd = False
                last_loaded = None
                continue

        for room in self.rooms.all():
            if hasattr(room.obj, "at_zone_reset"):
                room.obj.at_zone_reset()
                await sleep_for(0.01)