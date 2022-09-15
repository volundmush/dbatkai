from advent.legacy.zones import DefaultZone
from athanor.systems import System, sleep_for
from random import randint
import traceback


class ZoneSystem(System):
    name = "zone"
    interval = 1.0

    def __init__(self):
        super().__init__()
        self.zones = dict()

    def at_init(self):
        for z in DefaultZone.objects.all().order_by("id"):
            self.zones[z.id] = z
            if z.reset_countdown <= 0:
                z.reset_countdown = randint(5, 25)

    async def update(self):
        try:
            for k, v in self.zones.items():
                v.reset_countdown = v.reset_countdown - self.interval
                if v.reset_countdown <= 0:
                    await v.reset()
                    v.reset_countdown = v.lifespan * 60.0
        except Exception as err:
            traceback.print_exc(file=sys.stdout)


