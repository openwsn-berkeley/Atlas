import heapq
import itertools

class PriorityQueue:
    def __init__(self):
        self.elements =  []        # list of entries arranged in a heap
        self.entry_finder = {}               # mapping of tasks to entries
        self.REMOVED = '<removed-task>'      # placeholder for a removed task
        self.counter = itertools.count()     # unique sequence count

    def __contains__(self, item):
        return item in self.elements

    def empty(self):
        return len(self.elements) == 0

    def put(self, priority, item):
        'Add a new task or update the priority of an existing task'
        if item in self.entry_finder:
            self.remove_task(item)
        count = next(self.counter)
        entry = [priority, count, item]
        self.entry_finder[item] = entry
        heapq.heappush(self.elements, entry)

    def remove_task(self,item):
        'Mark an existing task as REMOVED.  Raise KeyError if not found.'
        entry = self.entry_finder.pop(item)
        entry[-1] = self.REMOVED

    def get(self):
        'Remove and return the lowest priority task. Raise KeyError if empty.'
        while self.elements:
            priority, count, item = heapq.heappop(self.elements)
            if item is not self.REMOVED:
                del self.entry_finder[item]
                return item
        raise KeyError('pop from an empty priority queue')