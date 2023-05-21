"""
Server startstop hooks

This module contains functions called by Evennia at various
points during its startup, reload and shutdown sequence. It
allows for customizing the server operation as desired.

This module must contain at least these global functions:

at_server_init()
at_server_start()
at_server_stop()
at_server_reload_start()
at_server_reload_stop()
at_server_cold_start()
at_server_cold_stop()

"""


def at_server_init():
    """
    This is called first as the server is starting up, regardless of how.
    """
    from django.conf import settings
    from collections import defaultdict
    from evennia.utils.utils import class_from_module, callables_from_module
    from advent import DG_FUNCTIONS, DG_VARS, DG_INSTANCE_CLASSES

    for k, v in settings.DG_INSTANCE_CLASSES.items():
        DG_INSTANCE_CLASSES[k] = class_from_module(v)

    for p in settings.DG_VARS:
        DG_VARS.update({k.lower(): v for k, v in callables_from_module(p).items()})

    dg_temp = defaultdict(dict)
    for category, mod_paths in settings.DG_FUNCTIONS.items():
        for func_path in mod_paths:
            for k, v in callables_from_module(func_path).items():
                dg_temp[category][k.lower()] = v
    shared = dict(dg_temp["shared"])

    for k, v in dg_temp.items():
        if k == "shared":
            continue
        DG_FUNCTIONS[k] = dict(shared)
        DG_FUNCTIONS[k].update(v)



def start_looping():
    from twisted.internet.task import LoopingCall
    from evennia.utils import class_from_module
    from athanor import LOOPING_DEFERREDS
    from django.conf import settings

    for name, data in settings.LOOPING_CALLS.items():
        callback = class_from_module(data['callback'])
        interval = data.get("interval", 10)
        looping_call = LoopingCall(callback)
        LOOPING_DEFERREDS[name] = looping_call
        looping_call.start(interval)


def at_server_start():
    """
    This is called every time the server starts up, regardless of
    how it was shut down.
    """
    start_looping()


def stop_looping():
    from athanor import LOOPING_DEFERREDS
    for looping_call in LOOPING_DEFERREDS.values():
        looping_call.stop()
    LOOPING_DEFERREDS.clear()


def at_server_stop():
    """
    This is called just before the server is shut down, regardless
    of it is for a reload, reset or shutdown.
    """
    stop_looping()


def at_server_reload_start():
    """
    This is called only when server starts back up after a reload.
    """
    pass


def at_server_reload_stop():
    """
    This is called only time the server stops before a reload.
    """
    pass


def at_server_cold_start():
    """
    This is called only when the server starts "cold", i.e. after a
    shutdown or a reset.
    """
    # Cleanup all AthanorPlayerCharacters that are online...
    # but can't be, because we crashed. This should put them all
    # into storage and update all time trackers.
    from athanor.typeclasses.characters import AthanorPlayerCharacter
    for obj in AthanorPlayerCharacter.objects.get_by_tag(key="puppeted", category="account"):
        if obj.db.is_online:
            obj.at_post_unpuppet(last_logout=obj.db.last_online, shutdown=True)


def at_server_cold_stop():
    """
    This is called only when the server goes down due to a shutdown or
    reset.
    """
    pass
