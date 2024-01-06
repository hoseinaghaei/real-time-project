import task
import task_dispatcher
import uunifast
from processor import Processor
from scheduler import Scheduler


def run(utilization: float):
    task_count = 50
    processor_count = 8
    processor_max_f = 1.6
    processor_min_f = 1.2
    scheduling_upperbound = 1200

    uunifast_utilization_list = uunifast.generate_uunifast_discard(utilization * processor_count, task_count)
    tasks = task.generate_tasks_from_utilization(uunifast_utilization_list, "task.csv")

    dispatched_tasks = task_dispatcher.dispatch_tasks(tasks, processor_count)

    processors = list(
        map(lambda x: Processor(x[0] + 1, [tasks[i] for i in x[1]], min_f=processor_min_f, max_f=processor_max_f),
            enumerate(dispatched_tasks)))
    scheduler = Scheduler(processors=processors, scheduling_upperbound=scheduling_upperbound)
    scheduler.schedule()
    logs = scheduler.get_logs()
    a = 1
    # todo : @HOSSEIN


if __name__ == '__main__':
    run(0.3)
