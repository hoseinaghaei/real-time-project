import math
from functools import reduce
from typing import Optional

from processor import Processor
from task import Instance


class Scheduler(object):
    def __init__(self, processors: list[Processor], scheduling_upperbound: Optional[int] = None,
                 time_partition: Optional[int] = 10):
        self.processors = processors
        self.scheduling_upperbound = scheduling_upperbound
        self.time_partition = time_partition
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
        return reduce(lambda x, y: x * y // math.gcd(x, y), periods, 1)

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
        if slack_scope < 1 or (end - start) // slack_scope < 1:
            return False, None, 1
        slack_count = (end - start) // slack_scope
        run_time = end - start
        ratio = max(run_time / (run_time + slack_count), p.min_f / p.max_f)
        run_time /= ratio
        return True, run_time, math.ceil(run_time) - (end - start)

    def _add_log(self, p: Processor, instance: Instance, start: int, end: int):
        if not instance:
            return 0

        log = {
            "instance_number": instance.number,
            "task_id": instance.task.id,
            "criticality": instance.task.criticality,
            "start_time": start,
        }
        if instance.first_run_time is None:
            instance.first_run_time = start
            log.update({
                'first_run_time': start,
                'arrival': instance.arrival
            })
        if instance.remaining_time == 0:
            log.update({
                'slack_time': instance.deadline - end
            })

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
        new_instances = set(filter(lambda x: x.arrival == self.time, self.ready_instances))
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

    @staticmethod
    def _pop_job_to_migrate(high_state_p: Processor, low_state_p: Processor, migrate_rate: int):
        high_state_p.tasks.sort(key=lambda p: p.utilization)
        if migrate_rate == 2:
            i = len(high_state_p.tasks) - 1
            while (low_state_p.get_utilization() + high_state_p.tasks[i].utilization > 1 or
                   (high_state_p.state['running_instance'] is not None and high_state_p.tasks[i] == high_state_p.state[
                       'running_instance'].task)):
                if i == 0:
                    return None, None, None
                i -= 1
            job = high_state_p.tasks.pop(i)

        else:
            i = 0
            while low_state_p.get_utilization() + high_state_p.tasks[i].utilization > 1 or (
                    high_state_p.state['running_instance'] is not None and high_state_p.tasks[i] == high_state_p.state[
                'running_instance'].task):
                i += 1
                if i == len(high_state_p.tasks):
                    return None, None, None

            job = high_state_p.tasks.pop(i)

        instances = set()
        ready_instances = set()
        for instance in high_state_p.state['ready_instances']:
            if instance.task != job:
                instances.add(instance)
            else:
                ready_instances.add(instance)

        high_state_p.state['ready_instances'] = instances

        instances = set()
        queue_instances = set()
        for instance in high_state_p.state['queue']:
            if instance.task != job:
                instances.add(instance)
            else:
                queue_instances.add(instance)

        high_state_p.state['queue'] = instances

        return job, ready_instances, queue_instances

    def _prepare_scheduler_after_feedback(self):
        processor_sorted_state = sorted(self.processors, key=lambda p: p.state['utilization'])
        for i in range(len(processor_sorted_state) // 2):
            high_state_p = processor_sorted_state[-i - 1]
            low_state_p = processor_sorted_state[i]
            state_diff = high_state_p.state['utilization'] - low_state_p.state['utilization']
            if state_diff > 0.2:
                migrate_rate = 2
            else:
                migrate_rate = 1

            job_to_migrate, ready_instances, queue_instances = self._pop_job_to_migrate(high_state_p, low_state_p,
                                                                                        migrate_rate)
            if job_to_migrate is not None:
                low_state_p.tasks.append(job_to_migrate)
                low_state_p.state['ready_instances'] = low_state_p.state['ready_instances'].union(ready_instances)
                low_state_p.state['queue'] = low_state_p.state['queue'].union(queue_instances)
                print(job_to_migrate)

    def _save_processor_state(self, p: Processor, partition: int):
        until_then = (partition + 1) * self.time_partition
        running_time = 0
        for log in self.run_logger[p]:
            if log['end_time'] > until_then:
                break
            running_time += log['end_time'] - log['start_time']

        p.state = {
            'utilization': running_time / self.time_partition,
            'queue': self.queue,
            'ready_instances': self.ready_instances,
            'running_instance': self.running_instance,
        }

    def _run_processors(self):
        for partition in range(math.ceil(self.scheduling_upperbound / self.time_partition)):
            if partition > 0:
                self._prepare_scheduler_after_feedback()
                self._add_hyper_periods()

            for p in self.processors:
                if partition == 0:
                    self._prepare_scheduler_for_processor(p)
                else:
                    self.queue = p.state['queue']
                    self.ready_instances = p.state['ready_instances']
                    self.running_instance = p.state['running_instance']

                time_slice_start = partition * self.time_partition
                self.time = partition * self.time_partition
                while self.time < ((partition + 1) * self.time_partition) and (self.queue or self.ready_instances):
                    self._run_instance_and_update_queue()
                    selected_instance = min(self.queue, key=lambda x: x.deadline) if self.queue else None
                    if selected_instance != self.running_instance:
                        added_time = self._add_log(p, self.running_instance, time_slice_start, self.time + 1)
                        for i in range(added_time):
                            self._increase_time_and_update_queue()
                        self.running_instance = selected_instance
                        time_slice_start = self.time + 1
                    self._increase_time_and_update_queue()

                self._save_processor_state(p, partition)

    def schedule(self):
        self._add_hyper_periods()
        self._add_jobs()
        self._calculate_slack_times()
        self._run_processors()

    def get_logs(self):
        return self.run_logger
