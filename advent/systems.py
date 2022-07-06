from advent import PENDING_COMMANDS, ZONE_TIMER
import asyncio
from advent.db.legacy.models import Zone, LegacyRoom
from evennia.prototypes.prototypes import search_prototype
from evennia.prototypes.spawner import spawn
from random import randint


async def execute_zone_reset(z: Zone):

    last_loaded = None
    last_cmd = False

    for cmd in z.commands.all().order_by("line"):
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

                    proto_list = search_prototype(key=f"legacy_mobile_{cmd.arg1}", require_single=True)
                    proto = proto_list[0]

                    # Roll the chance dice. if arg5 is 0 this will always succeed.
                    if not randint(1, 100) >= cmd.arg5:
                        last_cmd = False
                        last_loaded = None
                        continue

                    # arg4 is the max amount of mobiles that can be in this room.
                    if cmd.arg4 > 0:
                        total_amount = len([x for x in room.obj.contents if x.db.mobile_vnum == cmd.arg1])
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

                    proto_list = search_prototype(key=f"legacy_item_{cmd.arg1}", require_single=True)
                    proto = proto_list[0]

                    # Roll the chance dice. if arg5 is 0 this will always succeed.
                    if not randint(1, 100) >= cmd.arg5:
                        last_cmd = False
                        last_loaded = None
                        continue

                    # arg4 is the max amount of mobiles that can be in this room.
                    if cmd.arg4 > 0:
                        total_amount = len([x for x in room.obj.contents if x.db.item_vnum == cmd.arg1])
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
                    pass

                # Assign a variable.
                case "V":
                    pass

        except KeyError as err:
            last_cmd = False
            last_loaded = None
            continue


async def zone_reset():
    zone_ids = Zone.objects.all().values_list("id", flat=True).order_by("id")

    for zid in zone_ids:
        timer = ZONE_TIMER[zid]
        timer -= 1
        if timer <= 0:
            zone = Zone.objects.get(id=zid)
            await execute_zone_reset(zone)
            await asyncio.sleep(0.5)
            ZONE_TIMER[zid] = zone.lifespan * 60


async def command_queue():

    # First, copy the current pending commands and clear them.
    # this allows for new additions to PENDING_COMMANDS be made during iteration.
    pending = set(PENDING_COMMANDS)
    PENDING_COMMANDS.clear()

    for obj in pending:
        if obj.cmdqueue.check(0.1):
            # put any objects with commands still pending back into the queue.
            PENDING_COMMANDS.add(obj)
        await asyncio.sleep(0)

