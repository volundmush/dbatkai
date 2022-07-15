"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""
from athanor.typeclasses.characters import AthanorCharacter
from evennia.contrib.rpg.rpsystem import ContribRPCharacter
from evennia.utils.utils import lazy_property
from athanor.modifiers import FlagsHandler, FlagHandler
from .mixins import GameObj
from advent.handlers import PercentHandler, PowerStatHandler, PowerLevelHandler, StatHandler, \
    CharacterSizeHandler, PromptHandler, BoundedStatHandler
from advent.utils import INFLECT
from advent.typing import WearSlot

from rich.console import group
from rich.table import Table
from rich.text import Text
from rich.style import NULL_STYLE
from athanor.utils import ev_to_rich

from advent.sdesc import PCSdescHandler, PCRecogHandler
from advent.sdesc import NPCSdescHandler, NPCRecogHandler


class Character(GameObj, ContribRPCharacter, AthanorCharacter):
    """
    The Character defaults to reimplementing some of base Object's hook methods with the
    following functionality:

    at_basetype_setup - always assigns the DefaultCmdSet to this object type
                    (important!)sets locks so character cannot be picked up
                    and its commands only be called by itself, not anyone else.
                    (to change things, use at_object_creation() instead).
    at_after_move(source_location) - Launches the "look" command after every move.
    at_post_unpuppet(account) -  when Account disconnects from the Character, we
                    store the current location in the pre_logout_location Attribute and
                    move it to a None-location so the "unpuppeted" character
                    object does not need to stay on grid. Echoes "Account has disconnected"
                    to the room.
    at_pre_puppet - Just before Account re-connects, retrieves the character's
                    pre_logout_location Attribute and move it back on the grid.
    at_post_puppet - Echoes "AccountName has entered the game" to the room.

    """

    modifier_attrs = ["sensei", "race", "transformation", "mob_flags", "player_flags",
                      "admin_flags", "affect_flags"]

    @lazy_property
    def prompt(self):
        return PromptHandler(self)

    # power stats.
    @lazy_property
    def powerlevel(self):
        return PowerLevelHandler(self, "powerlevel", percent_name="powerlevel_perc")

    @lazy_property
    def stamina(self):
        return PowerStatHandler(self, "stamina", percent_name="stamina_perc")

    @lazy_property
    def ki(self):
        return PowerStatHandler(self, "ki", percent_name="ki_perc")

    # percent stats
    @lazy_property
    def suppress(self):
        return PercentHandler(self, "suppress")

    # normal stats.
    @lazy_property
    def strength(self):
        return StatHandler(self, "strength")

    @lazy_property
    def intelligence(self):
        return StatHandler(self, "intelligence")

    @lazy_property
    def constitution(self):
        return StatHandler(self, "constitution")

    @lazy_property
    def agility(self):
        return StatHandler(self, "agility")

    @lazy_property
    def wisdom(self):
        return StatHandler(self, "wisdom")

    @lazy_property
    def speed(self):
        return StatHandler(self, "speed")

    # traits
    @lazy_property
    def sensei(self):
        return FlagHandler(self, "sensei", "Sensei")

    @lazy_property
    def race(self):
        return FlagHandler(self, "race", "Race")

    @lazy_property
    def position(self):
        return FlagHandler(self, "position", "Position", default=8)

    @lazy_property
    def transformation(self):
        return FlagHandler(self, "transformation", "Transformation")

    @lazy_property
    def mob_flags(self):
        return FlagsHandler(self, "mob_flags", "MobFlags")

    @lazy_property
    def player_flags(self):
        return FlagsHandler(self, "player_flags", "PlayerFlags")

    @lazy_property
    def admin_flags(self):
        return FlagsHandler(self, "admin_flags", "AdminFlags")

    @property
    def gender(self):
        match self.db.sex:
            case 1:
                return "male"
            case 2:
                return "female"
            case _:
                return "neutral"

    # size
    @lazy_property
    def size(self):
        return CharacterSizeHandler(self)

    # weight
    def max_carry_weight(self, exist_value=None) -> float:
        if exist_value is None:
            exist_value = self.powerlevel.effective()
        return (exist_value / 200.0) + (self.strength.get() * 50.0)

    def speednar(self, exist_value=None) -> float:
        if exist_value is None:
            exist_value = self.powerlevel.effective()
        ratio = self.weight.burden() - self.max_carry_weight(exist_value=exist_value)
        if ratio >= .05:
            return max(0.01, min(1.0, 1.0-ratio))
        return 1.0

    def is_npc(self) -> bool:
        return True

    def revert_transformation(self, quiet=False):
        if (cur_form := self.transformation.get()):
            if not quiet:
                self.act(text=cur_form.echo_revert.format_map({"trans_name": cur_form.trans_name}))
        self.transformation.clear()

    def transform_to(self, form, quiet=False):
        if (found_form := self.transformation.set(form)):
            if not quiet:
                self.act(text=found_form.echo_transform)

    def get_display_name(self, looker, **kwargs):
        """
        Displays the name of the object in a viewer-aware manner.

        Args:
            looker (TypedObject): The object or account that is looking
                at/getting inforamtion for this object.

        Keyword Args:
            pose (bool): Include the pose (if available) in the return.
            ref (str): The reference marker found in string to replace.
                This is on the form #{num}{case}, like '#12^', where
                the number is a processing location in the string and the
                case symbol indicates the case of the original tag input
                - `t` - input was Titled, like /Tall
                - `^` - input was all uppercase, like /TALL
                - `v` - input was all lowercase, like /tall
                - `~` - input case should be kept, or was mixed-case
            noid (bool): Don't show DBREF even if viewer has control access.

        Returns:
            name (str): A string of the sdesc containing the name of the object,
                if this is defined. By default, included the DBREF if this user
                is privileged to control said object.

        """
        ref = kwargs.get("ref", "~")

        if looker == self:
            # always show your own key
            sdesc = self.db.color_name or self.key
        else:
            try:
                # get the sdesc looker should see
                sdesc = looker.get_sdesc(self, ref=ref)
            except AttributeError:
                # use own sdesc as a fallback
                sdesc = self.sdesc.get()

        sd = self.get_posed_sdesc(sdesc) if kwargs.get("pose", False) else sdesc
        build_string = self.generate_build_string(looker=looker, **kwargs)

        if hasattr(looker, "recog") and not looker.recog.get(self):
            sd = INFLECT.a(sd).capitalize()
        build_string.append(sd)
        return " ".join(build_string)

    def get_sdesc(self, obj, process=False, **kwargs):
        if self.is_npc() or obj.is_npc():
            return obj.db.color_name or obj.key
        else:
            if self.locks.check_lockstring(self, "perm(Builder)"):
                return obj.key
            return ContribRPCharacter.get_sdesc(self, obj, process=process, **kwargs)

    @group()
    def display_equipment(self, looker, show_empty=False, **kwargs):
        def row(s, obj):
            return ev_to_rich(f"|C<|c{slot.display():<20}|C>|n {obj.get_display_name(looker=looker) if obj else 'Nothing'}")

        for slot in WearSlot:
            if (eq := self.equipment.get(int(slot))) and looker.can_see(eq):
                yield row(slot, eq)
            elif show_empty:
                yield row(slot, eq)

    @group()
    def return_appearance(self, looker, **kwargs):
        if self.db.desc:
            yield ev_to_rich(self.db.desc)
            yield "\n"

        yield ev_to_rich("|WPHYS STUFF GOES HERE!|n")

        yield "\n"

        yield ev_to_rich("|wINFO GOES HERE!|n")

        any_eq = False
        for e in self.equipment.all():
            if looker.can_see(e):
                any_eq = True
                break

        if any_eq:
            yield "\n"
            yield ev_to_rich(f"{self.get_display_name(looker=looker)} is using:")
            yield self.display_equipment(looker, **kwargs)

    @lazy_property
    def bank_balance(self):
        return StatHandler(self, "bank_balance", default=0)

    @lazy_property
    def drunk(self):
        return BoundedStatHandler(self, "drunk", default=0, min_amt=0, max_amt=100)

    @lazy_property
    def hunger(self):
        return BoundedStatHandler(self, "hunger", default=100, min_amt=0, max_amt=100)

    @lazy_property
    def thirst(self):
        return BoundedStatHandler(self, "thirst", default=100, min_amt=0, max_amt=100)

    @lazy_property
    def experience(self):
        return StatHandler(self, "exp", default=0)

    @lazy_property
    def zenni(self):
        return StatHandler(self, "gold", default=0)

    @lazy_property
    def practices(self):
        return StatHandler(self, "practices", default=0)

    @lazy_property
    def sdesc(self):
        return NPCSdescHandler(self)

    @lazy_property
    def recog(self):
        return NPCRecogHandler(self)

class NonPlayerCharacter(Character):

    def get_vnum_display(self):
        if self.db.mobile_vnum:
            return f"|g[I-{self.db.mobile_vnum}]|n"
        return None

    def get_posed_sdesc(self, sdesc, **kwargs):
        """
        Displays the object with its current pose string.
        Returns:
            pose (str): A string containing the object's sdesc and
                current or default pose.
        """

        # get the current pose, or default if no pose is set
        pose = self.db.pose or self.db.pose_default

        # return formatted string, or sdesc as fallback
        old = f"{sdesc} {pose}" if pose else sdesc

        return self.db.room_description or old


class PlayerCharacter(Character):

    def is_npc(self) -> bool:
        return False

    @lazy_property
    def sdesc(self):
        return PCSdescHandler(self)

    @lazy_property
    def recog(self):
        return PCRecogHandler(self)
