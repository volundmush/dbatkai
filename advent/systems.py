from advent.legacy.zones import DefaultZone
from athanor.systems import System, sleep_for


class ZoneSystem(System):
    name = "zone"
    interval = 1.0

    def __init__(self):
        super().__init__()
        self.zones = dict()

    def at_init(self):
        for z in DefaultZone.objects.all().order_by("id"):
            self.zones[z.id] = z

    async def update(self):
        for k, v in self.zones.items():
            v.db_reset_countdown = v.db_reset_countdown - self.interval
            if v.db_reset_countdown <= 0:
                await v.reset()
                v.db_reset_countdown = v.db_lifespan * 60.0
