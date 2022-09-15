from commands.action import FightCommand, ActionCommand


class Equip(ActionCommand):
    key = "equipment"
    aliases = ["eq", "equ", "equip", "equipm", "equipme", "equipmen"]

    def func(self):
        self.caller.msg(text=self.caller.display_equipment(looker=self.caller, show_empty=True))