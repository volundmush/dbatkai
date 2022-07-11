from evennia.commands.default.muxcommand import MuxAccountCommand
from pathlib import Path
from advent.legacy.legacy import Importer


class CmdLegacyImport(MuxAccountCommand):
    key = "@import"
    locks = "cmd:superuser()"

    def func(self):
        if not self.args:
            self.msg("Must include a path to import from.")
            return

        p = Path(self.args)
        if not (p.exists() and p.is_dir()):
            self.msg("This doesn't look like a good path to me.")
            return

        a_path = p / "accounts"
        if not (a_path.exists() and a_path.is_dir()):
            self.msg("No accounts folder. This isn't a legacy folder.")
            return

        i = Importer(self.caller, p)
        self.caller.importer = i

        self.msg("Running legacy import. Hold on to your butts!")
        i.execute()
        self.msg("Import complete.")