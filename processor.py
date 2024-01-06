from task import Task


class Processor:
    def __init__(self, id: int, tasks: list[Task], min_f: float, max_f: float):
        self.id = id
        self.tasks = tasks
        self.min_f = min_f
        self.max_f = max_f
