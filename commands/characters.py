from commands.command import Command
from commands.action import FightCommand, ActionCommand
from advent.typing import Position
from advent.utils import partial_match, iequals


class Transform(FightCommand):
    key = "transform"

    def display_transformations(self, available):
        self.msg(f"TRANSFORM TABLE HERE! {available}")

    def func(self):
        if not (available := self.caller.race.get().get_available_transformations(self.caller)):
            self.msg("You... have transformations?")
            return

        if not self.args:
            self.display_transformations(available)
            return

        cur_form = self.caller.transformation.get()

        if iequals(self.args, "revert"):
            if not cur_form:
                self.msg("You are not transformed!")
                return
            if not cur_form.can_revert:
                self.msg("That would be unthinkable!")
                return

            self.caller.revert_transformation()
            return

        if not (found := partial_match(self.args, available, key=lambda x: x.get_name())):
            self.msg("You don't know how to become that.")
            return

        if not found.can_transform(self.caller):
            self.msg("You're not able to handle that form!")
            return

        self.caller.transform_to(found)
        self.caller.cmdqueue.set_wait(0.5)


class Equip(ActionCommand):
    key = "equipment"
    aliases = ["eq", "equ", "equip", "equipm", "equipme", "equipmen"]

    def func(self):
        self.caller.msg(text=self.caller.display_equipment(looker=self.caller, show_empty=True))