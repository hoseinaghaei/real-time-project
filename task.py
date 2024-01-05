from enum import Enum
import random
import csv


class Criticality(Enum):
    HARD = 1
    SOFT = 2


class Task(object):
    def __init__(self, id: int, utilization: float, period: int, execution_time: int, criticality: Criticality):
        self.id = id
        self.utilization = utilization
        self.period = period
        self.execution_time = execution_time
        self.criticality = criticality
        self.instances = []  # type of Instance

    def get_csv_row(self):
        return [self.id, self.execution_time, self.period, self.criticality, self.utilization]


class Instance:
    def __init__(self, task: Task, number: int):
        self.task = task
        self.number = number


def generate_tasks_from_utilization(utilization_list: list[float], csv_address: str = None) -> list[Task]:
    tasks = []
    task_id = 1
    for utilization in utilization_list:
        execution_time = int(random.uniform(1, 20))
        period = int(execution_time // utilization)
        criticality = random.choice([Criticality.HARD, Criticality.SOFT])
        task = Task(id=task_id, utilization=utilization, period=period, execution_time=execution_time,
                    criticality=criticality)
        tasks.append(task)
        task_id += 1

    if csv_address:
        with open(csv_address, 'w', newline='') as file:
            writer = csv.writer(file)

            writer.writerow(["ID", "Execution Time", "Period", "Criticality", "Utilization"])
            for task in tasks:
                writer.writerow(task.get_csv_row())

    return tasks
