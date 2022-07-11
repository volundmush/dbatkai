from django.db import models
from django.conf import settings
from evennia.typeclasses.models import TypedObject, SharedMemoryModel


class ZoneDB(TypedObject):
    __settingsclasspath__ = settings.BASE_ZONE_TYPECLASS
    __defaultclasspath__ = "advent.legacy.zones.DefaultZone"
    __applabel__ = "legacy"

    db_lifespan = models.IntegerField(default=0)
    db_reset_countdown = models.FloatField(default=0)
    db_start_vnum = models.IntegerField(default=0)
    db_end_vnum = models.IntegerField(default=0)
    db_reset_mode = models.SmallIntegerField(default=0)
    db_min_level = models.IntegerField(default=0)
    db_max_level = models.IntegerField(default=0)


class ResetCommand(models.Model):
    zone = models.ForeignKey(ZoneDB, on_delete=models.CASCADE, related_name="commands")
    line = models.IntegerField(default=0)

    command = models.CharField(max_length=1, null=False, blank=False)
    if_flag = models.BooleanField(default=False)
    arg1 = models.IntegerField(default=0)
    arg2 = models.IntegerField(default=0)
    arg3 = models.IntegerField(default=0)
    arg4 = models.IntegerField(default=0)
    arg5 = models.IntegerField(default=0)
    sarg1 = models.CharField(null=True, blank=True, max_length=255)
    sarg2 = models.CharField(null=True, blank=True, max_length=255)

    class Meta:
        unique_together = (("zone", "line"),)


class LegacyRoom(models.Model):
    zone = models.ForeignKey(ZoneDB, on_delete=models.CASCADE, related_name="rooms")
    obj = models.OneToOneField("objects.ObjectDB", related_name="legacy_room", on_delete=models.PROTECT)


class LegacyGuild(models.Model):
    zone = models.ForeignKey(ZoneDB, on_delete=models.CASCADE, related_name="guilds")
    skills = models.JSONField(default=None, null=True)
    feats = models.JSONField(default=None, null=True)
    charge = models.FloatField(default=1.0)
    no_such_skill = models.CharField(max_length=255)
    not_enough_gold = models.CharField(max_length=255)
    minlvl = models.IntegerField(default=0)
    gm = models.IntegerField(default=0)
    with_who = models.JSONField(default=None, null=True)
    time_open = models.IntegerField(default=0)
    time_close = models.IntegerField(default=0)


class LegacyShop(models.Model):
    zone = models.ForeignKey(ZoneDB, on_delete=models.CASCADE, related_name="shops")
    producing = models.JSONField(null=True)
    profit_buy = models.FloatField(default=1.0)
    profit_sell = models.FloatField(default=1.0)
    trade_types = models.JSONField(null=True)
    no_such_item1 = models.TextField(null=True, blank=True)
    no_such_item2 = models.TextField(null=True, blank=True)
    missing_cash1 = models.TextField(null=True, blank=True)
    missing_cash2 = models.TextField(null=True, blank=True)
    message_buy = models.TextField(null=True, blank=True)
    message_sell = models.TextField(null=True, blank=True)
    do_not_buy = models.TextField(null=True, blank=True)
    temper = models.IntegerField(default=0)
    shop_flags = models.JSONField(null=True)
    keeper = models.IntegerField(default=0)
    with_who = models.JSONField(default=None, null=True)
    time_open1 = models.IntegerField(default=0)
    time_close1 = models.IntegerField(default=0)
    time_open2 = models.IntegerField(default=0)
    time_close2 = models.IntegerField(default=0)
    bank_account = models.BooleanField(default=False)
    in_room = models.JSONField(null=True)
