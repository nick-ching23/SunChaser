import heapq

class Task:
    def __init__(self, id = -1, batch = 0, start = 0, end = 0, partitioned = False, time = float('inf')):
        self.id = id
        self.batch = batch
        self.start = start
        self.end = end
        self.partitioned = partitioned
        self.time = time
    
class PriorityQueue:
    def __init__(self):
        self.queue = []

    def push(self, task):
        heapq.heappush(self.queue, (task.time, task.start, task))

    def pop(self):
        if self.queue:
            return heapq.heappop(self.queue)[2]
        return None

    def __len__(self):
        return len(self.queue)

#workerid