# built-in
import threading
import time
import json
import os
# third-party
# local

# setup logging
import logging.config
import LoggingConfig
logging.config.dictConfig(LoggingConfig.LOGGINGCONFIG)
log = logging.getLogger('DataCollector')

class DataCollector(threading.Thread):
    '''
    Singleton, write to file periodically.
    '''
    
    # singleton pattern
    _instance = None
    _init     = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DataCollector, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, uname=None, filewriteperiod_s=10):

        # singleton pattern
        if self._init:
            return
        self._init = True

        #  handle params
        self.filewriteperiod_s    = filewriteperiod_s
        self.log_dir = "./logs"
        os.makedirs(self.log_dir, exist_ok=True)
        self.filename = None

        # local variables
        self.writebuffer          = []
        self.dataLock             = threading.RLock()

        # thread
        threading.Thread.__init__(self)
        self.name                 = 'DataCollector'
        self.daemon               = True
        self.start()

    def run(self):
        try:
            while True:
                # waits a bit
                time.sleep(self.filewriteperiod_s)

                # abort if no filename
                with self.dataLock:
                    if self.filename == None:
                        continue

                # write to the file
                with self.dataLock:
                    self._writeToFile()
        except Exception as err:
            log.error(err)

    # ======================== public ==========================================

    def setUame(self, uname):
        with self.dataLock:
            if self.filename:
                self._writeToFile()

            self.filename =  os.path.join(
                                self.log_dir,
                                '{}_{}.json'.format(
                                uname,
                                time.strftime("%y%m%d%H%M%S", time.localtime()),
                                )
                             )

    def collect(self, jsontocollect):
        with self.dataLock:
            self.writebuffer += [json.dumps(jsontocollect) + '\n']

    # ======================== private =========================================

    def _writeToFile(self):
        with open(self.filename, 'a') as f:
            while self.writebuffer:
                jsontocollect = self.writebuffer.pop(0)
                f.write(jsontocollect)

# ============================ main ============================================

def main():
    datacollector = DataCollector(0.100)
    time.sleep(0.100)
    datacollector.setFileName('data1.txt')
    time.sleep(0.100)
    datacollector.collect({'msg': 11})
    time.sleep(0.100)
    datacollector.collect({'msg': 12})
    time.sleep(0.100)
    datacollector.collect({'msg': 13})
    datacollector.collect({'msg': 14})
    time.sleep(0.100)
    datacollector.setFileName('data2.txt')
    time.sleep(0.100)
    datacollector.collect({'msg': 21})
    time.sleep(0.100)
    datacollector.collect({'msg': 22})
    time.sleep(0.100)
    datacollector.collect({'msg': 23})
    datacollector.collect({'msg': 24})
    time.sleep(3.100)

if __name__ == "__main__":
    main()
