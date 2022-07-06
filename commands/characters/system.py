from commands.command import Command


class ClearQueue(Command):
    key = "--"

    def func(self):
        match self.caller.cmdqueue.clear():
            case True:
                self.msg("Your command queue is cleared!")
            case False:
                self.msg("There are no commands to clear from your queue!")