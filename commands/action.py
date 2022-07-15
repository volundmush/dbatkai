from athanor.commands.queue import QueueCommand
from advent.typing import Position


class ActionCommand(QueueCommand):
    min_position = Position.DEAD

    def can_perform_command(self):
        if not self.caller.is_npc():
            if self.caller.player_flags.has("Goop"):
                self.msg("You only have your internal thoughts until your body has finished regenerating!")
                return False
            if self.caller.player_flags.has("Spiral"):
                self.msg("You are occupied with your Spiral Comet attack!")
                return False

        pos = self.caller.position.get()
        if pos.modifier_id < int(self.min_position):
            self.msg(pos.incap_message)
            return False

        return True

    def act(self, text=None, mapping=None, **kwargs):
        if self.caller.location:
            self.caller.location.msg_contents(text=text, exclude=[self.caller], from_obj=self.caller, mapping=mapping, **kwargs)


class FightCommand(ActionCommand):
    min_position = Position.FIGHTING


class StandCommand(ActionCommand):
    min_position = Position.STANDING


class RestingCommand(ActionCommand):
    min_position = Position.RESTING


class DeadCommand(ActionCommand):
    min_position = Position.DEAD


class SleepCommand(ActionCommand):
    min_position = Position.SLEEPING
