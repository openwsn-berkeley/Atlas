import pkg_resources
import toml
import threading

class BaseConfig(dict):
    """Thread-Safe Base Configuration Object"""
    lock = threading.Lock()

    def __init__(self, data):
        if isinstance(data, str):
            _dict = toml.load(data)
        elif isinstance(data, dict):
            _dict = data
        else:
            raise ValueError("Bad data type.")
        super().__init__(_dict)

    def __getattr__(self, *args):
        with self.lock:
            val = dict.get(self, *args)
            return BaseConfig(val) if type(val) is dict else val

    def __setattr__(self, *args, **kwargs):
        with self.lock:
            dict.__setitem__(*args, **kwargs)

    def __delattr__(self, *args, **kwargs):
        with self.lock:
            dict.__delitem__(*args, **kwargs)

class AtlasConfig(BaseConfig):
    def __init__(self, config="default", base=None):
        configpath = pkg_resources.resource_filename(__name__, f"resources/configs/{config}.toml")
        super().__init__(configpath)