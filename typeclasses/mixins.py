from advent.handlers import SizeHandler

from evennia.utils.utils import lazy_property
from evennia.utils.ansi import ANSIString

from evennia.utils.utils import to_str, logger, make_iter
from advent.utils import ev_to_rich
from advent.typing import Sex


class GameObj:

    def provides_light(self) -> bool:
        return False

    def is_illuminated(self) -> bool:
        return True

    @lazy_property
    def size(self):
        return SizeHandler(self)

    def get_vnum_display(self):
        return None

    def generate_build_string(self, looker=None, **kwargs):
        build_string = list()
        if not self.locks.check_lockstring(looker, "perm(Builder)"):
            return build_string
        if (vnum := self.get_vnum_display()):
            build_string.append(vnum)
        if (trigs := self.dgscripts.ids()):
            build_string.append(f"|g[T{','.join(str(t) for t in trigs)}]|n")
        build_string.append(f"|g[{self.dbref}]|n")
        return build_string

    def get_display_name(self, looker=None, **kwargs):
        build_string = self.generate_build_string(looker=looker, **kwargs)
        name = self.db.color_name or self.key
        build_string.append(name)
        return " ".join(build_string)

    def get_visible_sex(self, looker=None, **kwargs):
        return Sex.NEUTER

    def act(self, text=None, mapping=None, msg_type="pose", exclude=None, **kwargs):
        if self.location:
            self.location.msg_contents(text=(text, {"type": msg_type}), from_obj=self, mapping=mapping, exclude=exclude, **kwargs)
