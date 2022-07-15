from evennia.utils import ansi
from evennia.contrib.rpg.rpsystem.rpsystem import SdescHandler, RecogHandler, _RE_REF, _RE_SELF_REF, _RE_REF_LANG, _RE_LANGUAGE, _RE_OBJ_REF_START, SdescError


class NPCSdescHandler(SdescHandler):

    def _cache(self):
        pass

    def add(self, sdesc, max_length=60):
        return self.get()

    def get(self):
        return self.obj.key


class PCSdescHandler(NPCSdescHandler):

    def get(self):
        return self.obj.race.get().generate_sdesc()


class NPCRecogHandler(RecogHandler):

    def get(self, obj):
        return obj.key


class PCRecogHandler(RecogHandler):

    def get(self, obj):
        if obj.is_npc():
            return obj.key
        if self.obj == obj:
            return self.obj.key
        if self.obj.locks.check_lockstring(self.obj, "perm(Helper)"):
            return obj.key
        return super().get(obj)
