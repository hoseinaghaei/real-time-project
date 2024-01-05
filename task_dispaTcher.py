from task import Task
import binpacking


def dispatch_tasks(tasks: list[Task], processor_count: int) -> list:
    task_index_to_utilization = dict(map(lambda x: (x[0], x[1].utilization), enumerate(tasks)))
    print(task_index_to_utilization)
    return binpacking.to_constant_bin_number(task_index_to_utilization, processor_count)
