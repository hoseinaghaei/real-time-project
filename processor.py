from task import Task


class Processor:
    def __init__(self, id: int, tasks: list[Task]):
        self.id = id
        self.tasks = tasks
