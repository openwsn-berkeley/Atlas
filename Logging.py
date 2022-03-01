import threading
import time
import json


class PeriodicFileLogger(threading.Thread):
    # singleton pattern
    _instance = None
    _init = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PeriodicFileLogger, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, filewriteperiod_s=10):

        # singleton pattern
        if self._init:
            return
        self._init = True

        #  handle params
        self.filewriteperiod_s = filewriteperiod_s

        # local variables
        self.writebuffer = []
        self.filename = None
        self.dataLock = threading.RLock()

        # thread
        threading.Thread.__init__(self)
        self.name = 'PeriodicFileLogger'
        self.daemon = True
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
            print(err)

    # ======================== public ==========================================

    def setFileName(self, filename):
        with self.dataLock:
            if self.filename != None:
                self._writeToFile()
            self.filename = filename

    def log(self, jsontolog):
        with self.dataLock:
            self.writebuffer += [json.dumps(jsontolog) + '\n']

    # ======================== private =========================================

    def _writeToFile(self):
        with open(self.filename, 'a') as f:
            while self.writebuffer:
                jsontolog = self.writebuffer.pop(0)
                f.write(jsontolog)


# ============================ main ============================================

def main():
    periodicFileLogger = PeriodicFileLogger(0.100)
    time.sleep(0.100)
    periodicFileLogger.setFileName('log1.txt')
    time.sleep(0.100)
    periodicFileLogger.log({'msg': 11})
    time.sleep(0.100)
    periodicFileLogger.log({'msg': 12})
    time.sleep(0.100)
    periodicFileLogger.log({'msg': 13})
    periodicFileLogger.log({'msg': 14})
    time.sleep(0.100)
    periodicFileLogger.setFileName('log2.txt')
    time.sleep(0.100)
    periodicFileLogger.log({'msg': 21})
    time.sleep(0.100)
    periodicFileLogger.log({'msg': 22})
    time.sleep(0.100)
    periodicFileLogger.log({'msg': 23})
    periodicFileLogger.log({'msg': 24})
    time.sleep(3.100)


if __name__ == "__main__":
    main()