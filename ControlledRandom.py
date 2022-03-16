import random
import Logging

class ControlledRandom(random.Random):
    # singleton pattern
    _instance = None
    _init = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ControlledRandom, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, x=None):

        # singleton pattern
        if self._init:
            return
        self._init = True

        self.logger = Logging.PeriodicFileLogger()
        self.seed(x)
        state_data = {"type": "random_seed_state", "sate_data": self.getstate()}
        self.logger.log(state_data)

        self.gauss_next = None