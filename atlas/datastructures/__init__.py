import heapq

class PriorityQueue:
    def __init__(self):
        self.elements = []
        self.check = set()

    def __contains__(self, item):
        assert len(self.elements) >= len(self.check)
        return item in self.check

    def empty(self):
        assert len(self.elements) >= len(self.check)
        return len(self.elements) == 0

    def put(self, priority, item):
        if item not in self.check:
            heapq.heappush(self.elements, (priority, item))
            self.check.add(item)
        assert len(self.elements) >= len(self.check)

    def get(self):
        item = heapq.heappop(self.elements)[1]
        self.check.remove(item)
        return item
