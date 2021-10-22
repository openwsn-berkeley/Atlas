import heapq
import itertools

class PriorityQueue:
    def __init__(self):
        self.elements =  []          # list of entries arranged in a heap
        self.entry_finder = {}       # mapping of tasks to entries
        self.REMOVED = object()      # placeholder for a removed task

    def __contains__(self, item):
        return item in self.elements

    def empty(self):
        return len(self.elements) == 0

    def put(self, priority, item):
        # Add a new task or update the priority of an existing task

        if item in self.entry_finder:
            previous_entry = self.entry_finder[item]
            previous_priority = previous_entry[0]
            if priority < previous_priority:
                previous_entry[-1] = self.REMOVED

        self.entry_finder[item] = [priority, item]
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        # Remove and return the lowest priority task. Raise KeyError if empty
        while self.elements:
            item = heapq.heappop(self.elements)[1]
            if item is not self.REMOVED:
                try:
                    del self.entry_finder[item]
                except KeyError:
                    continue
                return item
            else:
                pass
        raise KeyError('pop from an empty priority queue')