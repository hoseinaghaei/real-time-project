import math
from functools import reduce
from typing import Optional

from processor import Processor
from task import Instance


class Scheduler(object):
    def __init__(self, processors: list[Processor], scheduling_upperbound: Optional[int] = None):
        self.processors = processors
        self.scheduling_upperbound = scheduling_upperbound
        self.hyper_period_mapper = {p: None for p in self.processors}
        self.slack_time_mapper = {p: None for p in self.processors}
        self.run_logger = {p: [] for p in self.processors}
        self.queue = set()
        self.time = 0
        self.ready_instances = set()
        self.running_instance = None

    @staticmethod
    def _find_hyper_period(processor: Processor):
        periods = {t.period for t in processor.tasks}
        return reduce(lambda x, y: x * y // math.gcd(x, y), periods)

    def _add_hyper_periods(self):
        for p in self.processors:
            self.hyper_period_mapper[p] = self._find_hyper_period(p)

    def _add_jobs(self):
        for p in self.processors:
            hyper_period = self.hyper_period_mapper[p]
            upper_bound = self.scheduling_upperbound or hyper_period
            for t in p.tasks:
                multiples = list()
                mul = 0
                while mul <= upper_bound:
                    multiples.append(mul)
                    mul += t.period
                multiples = list(filter(lambda x: x <= upper_bound, multiples))
                for idx, m in enumerate(multiples):
                    t.instances.append(
                        Instance(number=idx, task=t, arrival=m, deadline=m + t.period, exec_time=t.execution_time)
                    )

    def _calculate_slack_times(self):
        for p in self.processors:
            total_exec_time = sum(len(t.instances) * t.execution_time for t in p.tasks)
            slack_time = self.hyper_period_mapper[p] - total_exec_time
            self.slack_time_mapper[p] = slack_time

    def _has_slack(self, p: Processor, start: int, end: int):
        if self.slack_time_mapper[p] == 0:
            return False, None, 1
        slack_scope = math.ceil(self.hyper_period_mapper[p] / self.slack_time_mapper[p])
        slack_count = (end - start) // slack_scope
        if slack_count < 1:
            return False, None, 1
        run_time = end - start
        ratio = max(run_time / (run_time + slack_count), p.min_f / p.max_f)
        run_time /= ratio
        return True, run_time, math.ceil(run_time) - (end - start)

    def _add_log(self, p: Processor, instance: Instance, start: int, end: int):
        log = {
            "instance_number": instance.number,
            "task_id": instance.task.id,
            "start_time": start,
        }
        has_slack, new_exec_time, added_time = self._has_slack(p, start, end)
        if has_slack:
            log.update({
                "has_slack": True,
                "end_time": start + new_exec_time,
                "added_slack": new_exec_time - (end - start),
            })
        else:
            log.update({
                "end_time": end
            })

        self.run_logger[p].append(log)

        return added_time

    def _increase_time_and_update_queue(self):
        self.time += 1
        new_instances = set(filter(lambda x: x == self.time, self.ready_instances))
        self.ready_instances -= new_instances
        self.queue.update(new_instances)

    def _prepare_scheduler_for_processor(self, p: Processor):
        self.time = 0
        self.ready_instances = set()
        for t in p.tasks:
            self.ready_instances = self.ready_instances.union(set(t.instances))
        self.queue = set(filter(lambda x: x.arrival == 0, self.ready_instances))
        self.ready_instances -= self.queue
        self.running_instance = min(self.queue, key=lambda x: x.deadline)

    def _run_instance_and_update_queue(self):
        if not self.running_instance:
            return
        self.running_instance.remaining_time -= 1
        if self.running_instance.remaining_time == 0:
            self.queue.remove(self.running_instance)

    def _run_processors(self):
        for p in self.processors:
            self._prepare_scheduler_for_processor(p)
            time_slice_start = 0
            simulation_time = self.scheduling_upperbound or self.hyper_period_mapper[p]
            while self.time < simulation_time:
                self._run_instance_and_update_queue()
                selected_instance = min(self.queue, key=lambda x: x.deadline) if self.queue else None
                if selected_instance != self.running_instance:
                    added_time = self._add_log(p, self.running_instance, time_slice_start, self.time + 1)
                    for i in range(added_time):
                        self._increase_time_and_update_queue()
                    self.running_instance = selected_instance
                    time_slice_start = self.time + 1
                self._increase_time_and_update_queue()

    def schedule(self):
        self._add_hyper_periods()
        self._add_jobs()
        self._calculate_slack_times()
        self._run_processors()

    def get_logs(self):
        return self.run_logger
