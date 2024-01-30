import random
import matplotlib.pyplot as plt

from task import Criticality


class DiagramDisplayer(object):

    @staticmethod
    def _random_color():
        return "#" + "".join([random.choice("0123456789ABCDEF") for _ in range(6)])

    @classmethod
    def _set_colors(cls, data: dict):
        ids = set()
        for core in data:
            core_data = data[core]
            for i in core_data:
                ids.add(i["task_id"])
        return {i: cls._random_color() for i in ids}

    @classmethod
    def _draw_schedule(cls, data: dict, colors: dict):
        fig, axs = plt.subplots(8, 1, figsize=(20, 8), sharex=True)
        for core, ax in zip(data, axs):
            p_data = data[core]
            end_time = int(max(p_data, key=lambda x: x["end_time"])["end_time"])
            for i in p_data:
                ax.bar(
                    i["start_time"], 1,
                    i["end_time"] - i["start_time"],
                    align='edge', edgecolor='grey', fill=True,
                    color=colors[i["task_id"]]
                )
                text_position = (i["start_time"] + i["end_time"]) / 2
                ax.text(text_position, 0.5, i['task_id'], ha='center', va='center', color='black', fontsize=10,
                        fontweight='bold')

            ax.set_ylabel(f'CORE {core.id}')
            ax.set_xlim(0, end_time)
            ax.set_ylim(0, 1)
            ax.set_xticks(range(0, end_time))
            ax.grid(True, which='both', axis='x', linestyle='--', linewidth=1)

    @classmethod
    def _merge_logs(cls, data: dict):
        logs = []
        for p in data:
            core_data = data[p]
            logs = [*logs, *core_data]
        return logs

    @classmethod
    def _draw_mean_waiting_time(cls, data: dict):
        logs = cls._merge_logs(data)
        filtered_logs = list(filter(lambda x: x.get("first_run_time") is not None, logs))
        end_time = max(filtered_logs, key=lambda x: x["end_time"])["end_time"]
        nums = [5 * i for i in range(1, int(end_time // 5) + 1)]
        dots = []
        for i in nums:
            matched_logs = list(filter(lambda x: i > x.get("first_run_time") >= i - 5, filtered_logs))
            waiting_times = [j["first_run_time"] - j["arrival"] for j in matched_logs] if matched_logs else [0]
            mean = round(sum(waiting_times) / len(waiting_times))
            dots.append((i, mean))

        x, y = zip(*dots)
        plt.figure(figsize=(8, 4))
        plt.scatter(x, y)
        plt.plot(x, y)
        plt.xlabel('time')
        plt.ylabel('mean')
        plt.title('Mean waiting time')
        plt.grid(True)

    @classmethod
    def _draw_mean_slack_time(cls, data: dict):
        logs = cls._merge_logs(data)
        filtered_logs = list(filter(lambda x: x.get("slack_time") is not None, logs))
        end_time = max(filtered_logs, key=lambda x: x["end_time"])["end_time"]
        nums = [5 * i for i in range(1, int(end_time // 5) + 1)]
        dots = []
        for i in nums:
            matched_logs = list(filter(lambda x: i > x.get("slack_time") >= i - 5, filtered_logs))
            slack_times = [j.get("slack_time") for j in matched_logs] if matched_logs else [0]
            mean = round(sum(slack_times) / len(slack_times))
            dots.append((i, mean))

        x, y = zip(*dots)
        plt.figure(figsize=(8, 4))
        plt.scatter(x, y)
        plt.plot(x, y)
        plt.xlabel('time')
        plt.ylabel('mean')
        plt.title('Mean slack.png time')
        plt.grid(True)

    @classmethod
    def draw(cls, data: dict, scheduling_upperbound: int):
        colors = cls._set_colors(data)

        cls._draw_schedule(data, colors)
        cls._draw_mean_waiting_time(data)
        cls._draw_mean_slack_time(data)
        cls.makespan(data, scheduling_upperbound)

        plt.tight_layout()
        plt.show()

    @classmethod
    def makespan(cls, data: dict, scheduling_upperbound: int):
        fig, ax = plt.subplots(figsize=(len(data) * 2, 8))

        core_numbers = [core.id for core in data]
        makespans = [min(scheduling_upperbound, max(p_data, key=lambda x: x["end_time"])["end_time"] -
                         min(p_data, key=lambda x: x["start_time"])["start_time"]) for p_data in data.values()]

        ax.bar(
            core_numbers, makespans,
            align='center', edgecolor='grey', fill=True,
            color=[cls._random_color() for _ in range(len(data))]
        )

        ax.set_xlabel('CORE Number')
        ax.set_ylabel('Makespan')
        ax.set_title('Columnar Makespan for Cores')
        ax.grid(True, which='both', axis='y', linestyle='--', linewidth=1)