from .command import Command


class ActionCommand(Command):
    min_position = 0

    def at_pre_cmd(self):
        if getattr(self.caller, "is_player", False):
            if self.caller.tags.has(category="player_flags", key="Goop"):
                self.msg("You only have your internal thoughts until your body has finished regenerating!")
                return True
            if self.caller.tags.has(category="player_flags", key="Spiral"):
                self.msg("You are occupied with your Spiral Comet attack!")
                return True

        pos = self.caller.aspects.get_aspect("position")
        if int(pos) < int(self.min_position):
            self.msg(pos.incap_message)
            return True

        return False

    def act(self, text=None, mapping=None, **kwargs):
        if self.caller.location:
            self.caller.location.msg_contents(text=text, exclude=[self.caller], from_obj=self.caller, mapping=mapping, **kwargs)


class FightCommand(ActionCommand):
    min_position = 7


class StandCommand(ActionCommand):
    min_position = 8


class RestingCommand(ActionCommand):
    min_position = 5


class DeadCommand(ActionCommand):
    min_position = 0


class SleepCommand(ActionCommand):
    min_position = 4