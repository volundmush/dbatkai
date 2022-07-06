from evennia.server.serversession import ServerSession
from evennia.utils.utils import lazy_property
from advent.handlers.session import PromptHandler


class AdventSession(ServerSession):

    @lazy_property
    def console(self):
        from mudrich import MudConsole
        return MudConsole(color_system=self.rich_color_system(), width=self.protocol_flags["SCREENWIDTH"][0],
                          file=self, record=True)

    def rich_color_system(self):
        if self.protocol_flags["NOCOLOR"]:
            return None
        if self.protocol_flags["XTERM256"]:
            return "256"
        if self.protocol_flags["ANSI"]:
            return "standard"

    def write(self, b: str):
        """
        When self.console.print() is called, it writes output to here.
        Not necessarily useful, but it ensures console print doesn't end up sent out stdout or etc.
        """

    def flush(self):
        """
        Do not remove this method. It's needed to trick Console into treating this object
        as a file.
        """

    def print(self, *args, **kwargs) -> str:
        """
        A thin wrapper around Rich.Console's print. Returns the exported data.
        """
        self.console.print(*args, highlight=False, **kwargs)
        return self.console.export_text(clear=True, styles=True)

    def msg(self, text=None, **kwargs):
        if text is not None:
            if hasattr(text, "__rich_console__"):
                text = self.print(text)
        super().msg(text=text, **kwargs)

    def data_out(self, **kwargs):
        if (t := kwargs.get("text", None)):
            if hasattr(t, "__rich_console__"):
                kwargs["text"] = self.print(t)
            if self.puppet:
                self.prompt.prepare()
        super().data_out(**kwargs)

    @lazy_property
    def prompt(self):
        return PromptHandler(self)