from advent.handlers.basic import EquipmentHandler, InventoryHandler, WeightHandler, SizeHandler
from advent.handlers.basic import CmdQueueHandler, PromptHandler

from evennia.utils.utils import lazy_property
from evennia.utils.ansi import ANSIString
from evennia.contrib.rpg.traits import TraitHandler

from evennia.utils.utils import to_str, logger, make_iter
from advent.utils import ev_to_rich, echo_action
from advent.typing import Sex


class GameObj:
    modifier_attrs = []

    @lazy_property
    def prompt(self):
        return PromptHandler(self)

    @lazy_property
    def cmdqueue(self):
        return CmdQueueHandler(self)

    @lazy_property
    def traits(self):
        return TraitHandler(self)

    def get_all_modifiers(self):
        for attr in self.modifier_attrs:
            if hasattr(self, attr):
                for m in getattr(self, attr).all():
                    yield m

        for obj in self.equipment.all():
            for m in obj.get_all_modifiers():
                yield m

    @lazy_property
    def inventory(self):
        return InventoryHandler(self)

    @lazy_property
    def equipment(self):
        return EquipmentHandler(self)

    @lazy_property
    def weight(self):
        return WeightHandler(self)

    def provides_light(self) -> bool:
        return False

    def is_illuminated(self) -> bool:
        return True

    def max_carry_weight(self, exist_value=None) -> float:
        return 9999999999999999999999999999.0

    def available_carry_weight(self, exist_value=None) -> float:
        return self.max_carry_weight(exist_value=exist_value) - self.weight.burden()

    @lazy_property
    def size(self):
        return SizeHandler(self)

    def msg(self, text=None, from_obj=None, session=None, options=None, **kwargs):
        # try send hooks
        if from_obj:
            for obj in make_iter(from_obj):
                try:
                    obj.at_msg_send(text=text, to_obj=self, **kwargs)
                except Exception:
                    logger.log_trace()
        kwargs["options"] = options
        try:
            if not self.at_msg_receive(text=text, from_obj=from_obj, **kwargs):
                # if at_msg_receive returns false, we abort message to this object
                return
        except Exception:
            logger.log_trace()

        if text is not None:
            if not isinstance(text, str):
                if isinstance(text, tuple):
                    first = text[0]
                    if hasattr(first, "__rich_console__"):
                        kwargs["text"] = first
                    elif isinstance(first, str):
                        kwargs["text"] = first
                    else:
                        try:
                            kwargs["text"] = to_str(first)
                        except Exception:
                            kwargs["text"] = repr(first)
                elif hasattr(text, "__rich_console__"):
                    kwargs["text"] = text
                else:
                    try:
                        kwargs["text"] = to_str(text)
                    except Exception:
                        kwargs["text"] = repr(text)
            else:
                kwargs["text"] = text


        # relay to session(s)
        sessions = make_iter(session) if session else self.sessions.all()
        for session in sessions:
            session.data_out(**kwargs)

    def at_object_leave(self, moved_obj, target_location, **kwargs):
        if moved_obj.db.equipped:
            self.equipment.remove(moved_obj.db.equipped)
        else:
            self.inventory.remove(moved_obj)

    def at_object_receive(self, moved_obj, source_location, **kwargs):
        self.inventory.add(moved_obj)

    def at_pre_get(self, getter, **kwargs):
        total_weight = self.weight.total()
        if total_weight > getter.available_carry_weight():
            getter.msg(ev_to_rich(f"You can't carry {self.get_display_name(looker=getter)}! (Weight: {total_weight})"))
            return False
        return True

    def get_vnum_display(self):
        return None

    def generate_build_string(self, looker=None, **kwargs):
        build_string = list()
        if not self.locks.check_lockstring(looker, "perm(Builder)"):
            return build_string
        if (vnum := self.get_vnum_display()):
            build_string.append(vnum)
        if self.db.triggers:
            build_string.append(f"|g[T{','.join(str(t) for t in self.db.triggers)}]|n")
        build_string.append(f"|g[{self.dbref}]|n")
        return build_string

    def get_visible_sex(self, looker=None, **kwargs):
        return Sex.NEUTER

    def act(self, text=None, mapping=None, **kwargs):
        if self.location:
            self.location.msg_contents(text=text, from_obj=self, mapping=mapping, **kwargs)