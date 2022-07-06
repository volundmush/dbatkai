"""
Server startstop hooks

This module contains functions called by Evennia at various
points during its startup, reload and shutdown sequence. It
allows for customizing the server operation as desired.

This module must contain at least these global functions:

at_server_start()
at_server_stop()
at_server_reload_start()
at_server_reload_stop()
at_server_cold_start()
at_server_cold_stop()

"""


def at_server_start():
    """
    This is called every time the server starts up, regardless of
    how it was shut down.
    """
    from mudrich import install_mudrich
    install_mudrich()

    from evennia.utils.utils import callables_from_module, delay
    from django.conf import settings
    from advent import MODIFIERS_ID, MODIFIERS_NAMES, SYSTEMS

    for mod_path in settings.MODIFIER_PATHS:
        for k, v in callables_from_module(mod_path).items():
            MODIFIERS_NAMES[v.category][v.get_name()] = v
            MODIFIERS_ID[v.category][v.mod_id] = v

    from advent.systems import zone_reset, command_queue
    from twisted.internet import task
    from twisted.internet.defer import Deferred

    zres = task.LoopingCall(lambda: Deferred.fromCoroutine(zone_reset()))
    cqueue = task.LoopingCall(lambda: Deferred.fromCoroutine(command_queue()))

    SYSTEMS[zres] = zres.start(1.0)
    SYSTEMS[cqueue] = cqueue.start(0.1)


def at_server_stop():
    """
    This is called just before the server is shut down, regardless
    of it is for a reload, reset or shutdown.
    """
    pass


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
    pass


def at_server_cold_stop():
    """
    This is called only when the server goes down due to a shutdown or
    reset.
    """
    pass
