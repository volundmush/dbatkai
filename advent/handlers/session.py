from twisted.internet import reactor, task


class PromptHandler:

    def __init__(self, owner):
        self.owner = owner
        self.task = None

    def prepare(self):
        if self.task:
            self.task.cancel()
        self.task = task.deferLater(reactor, 0.1, self.print)
        self.task.addErrback(self.error)

    def print(self):
        if self.owner.puppet:
            self.owner.msg(prompt=f"\n{self.owner.puppet.prompt.render()}\n")

    def error(self, err):
        pass