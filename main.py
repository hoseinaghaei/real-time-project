import task
import task_dispaTcher
import uunifast
from processor import Processor


def run(utilization: float):
    task_count = 100
    processor_count = 8

    uunifast_utilization_list = uunifast.generate_uunifast_discard(utilization * processor_count, task_count)
    tasks = task.generate_tasks_from_utilization(uunifast_utilization_list, "task.csv")

    dispatched_tasks = task_dispaTcher.dispatch_tasks(tasks, processor_count)

    processors = list(map(lambda x: Processor(x[0] + 1, [tasks[i] for i in x[1]]), enumerate(dispatched_tasks)))
    print(processors)
    # todo : @ARMIN


if __name__ == '__main__':
    run(0.3)
