from .action import RestingCommand


class Give(RestingCommand):
    """
    Give an item from your inventory to someone else.

    Usage:
        give <object> <target>

    Note:
          Can be used with all. or #. prefix.
          Example: give all.meat <target>

    Note:
        Most NPCs will reject items. But, some may
        desire them as part of quests. Don't be afraid
        to try.
    """
    key = "give"

    def func(self):
        if not self.caller.location:
            self.caller.msg("You are nowhere! There is nobody to gift anything to!")
            return

        if not self.args:
            self.msg("Usage: give <object> <target>")
            return

        args = self.args.split()
        if not len(args) == 2:
            self.msg("Usage: give <object> <target>")
            return

        if not (items := self.caller.search(args[0], candidates=self.caller.inventory.all(), allow_multiple=True)):
            self.msg(f"You don't have a {args[0]}")
            return

        if not (target := self.caller.search(args[1], candidates=self.caller.get_visible_nearby(obj_type="character"))):
            self.msg(f"You don't see any {args[1]}")
            return

        for item in items:
            if not item.at_pre_give(self.caller, target):
                continue
            if not item.move_to(target, move_type="give"):
                continue
            item.at_give(self.caller, target)


class Get(RestingCommand):
    key = "get"

    def func(self):

        if not self.args:
            self.msg("Usage: get <object> [<container>]")
            return

        args = self.args.split()
        if not len(args) in (1, 2):
            self.msg("Usage: get <object> [<container>]")
            return

        if len(args) == 3:
            target_candidates = self.caller.equipment.all() + self.caller.inventory.all()
            if self.caller.location:
                target_candidates.extend(self.caller.get_visible_nearby(obj_type="item"))
            if not (target := self.caller.search(args[2], candidates=target_candidates, allow_multiple=True)):
                self.msg(f"You don't see any {args[2]}")
                return
        else:
            if not self.caller.location:
                self.caller.msg("You are nowhere! There is nowhere to get anything from!")
                return
            target = [self.caller.location]

        for t in target:
            if not (items := self.caller.search(args[0], candidates=self.caller.filter_visible(t.inventory.all()), allow_multiple=True)):
                self.msg(f"{t.get_display_name(looker=self.caller)} doesn't have a {args[0]}")
                continue

            for i in items:
                if not i.at_pre_get(self.caller):
                    continue
                if i.move_to(self.caller, move_type="get"):
                    i.at_get(self.caller)


class Drop(RestingCommand):
    key = "drop"

    def func(self):
        if not self.caller.location:
            self.caller.msg("You are nowhere! It would be unwise to drop anything here. Wherever 'here' is...")
            return

        arg = self.args.strip()

        if not arg:
            self.msg("Usage: drop <object>")

        if not (items := self.caller.search(arg, candidates=self.caller.inventory.all(), allow_multiple=True)):
            self.msg(f"You don't have a {arg}")
            return

        for i in items:
            if not i.at_pre_drop(self.caller):
                continue

            if i.move_to(self.caller.location, move_type="drop"):
                i.at_drop(self.caller)


class Put(RestingCommand):
    key = "put"

    def func(self):

        if not self.args:
            self.msg("Usage: put <object> <container>")
            return

        args = self.args.split()
        if not len(args) == 2:
            self.msg("Usage: put <object> <container>")
            return

        if not (items := self.caller.search(args[0], candidates=self.caller.inventory.all(), allow_multiple=True)):
            self.msg(f"You don't have a {args[0]}")
            return

        candidates = list()
        candidates.extend(self.caller.equipment.all())
        candidates.extend(self.caller.inventory.all())
        if self.caller.location:
            candidates.extend(self.caller.get_visible_nearby(obj_type="item"))

        if not (target := self.caller.search(args[1], candidates=candidates)):
            self.msg(f"You don't see any {args[1]}")
            return

        for item in items:
            if not item.at_pre_give(self.caller, target):
                continue
            if not item.move_to(target, move_type="put"):
                continue
            item.at_give(self.caller, target)


class Wield(RestingCommand):
    key = "wield"


class Wear(RestingCommand):
    key = "wear"


class Hold(RestingCommand):
    key = "hold"
    aliases = ["grab"]


class Remove(RestingCommand):
    key = "remove"