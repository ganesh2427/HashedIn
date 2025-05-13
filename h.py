class TaskScheduler:
    def __init__(self):
        self.task_heap = []
        self.task_counter = 0

    def submitTask(self, task,estimated_time):
        heapq.heappush(self.task_heap,estimatedTime,taskId)

    def getNextTaskToProcess(self):
        if self.task_heap:
            estimatedTime,taskId = heapq.heappop(self.task_heap)
            return taskId
        else:
            return None