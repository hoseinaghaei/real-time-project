import random
import matplotlib.pyplot as plt

from task import Criticality


class DiagramDisplayer(object):

    @staticmethod
    def _random_color():
        return "#" + "".join([random.choice("0123456789ABCDEF") for _ in range(6)])

    @staticmethod
    def _extract_task_ids(core_data: list):
        return {i["task_id"] for i in core_data}

    @classmethod
    def _set_colors(cls, core_data: list):
        return {i: cls._random_color() for i in cls._extract_task_ids(core_data)}

    @classmethod
    def draw(cls, data: dict):
        fig, axs = plt.subplots(8, 1, figsize=(20, 8), sharex=True)

        for core, ax in zip(data, axs):
            p_data = data[core]
            colors = cls._set_colors(p_data)
            end_time = int(max(p_data, key=lambda x: x["end_time"])["end_time"])
            for i in p_data:
                ax.bar(
                    i["start_time"], 1,
                    i["end_time"] - i["start_time"],
                    align='edge', edgecolor='grey', fill=True,
                    color=colors[i["task_id"]]
                )
                if i["criticality"] == Criticality.HARD:
                    text_position = (i["start_time"] + i["end_time"]) / 2
                    ax.text(text_position, 0.5, "H", ha='center', va='center', color='black', fontsize=10,
                            fontweight='bold')

            ax.set_ylabel(f'CORE {core.id}')
            ax.set_xlim(0, end_time)
            ax.set_ylim(0, 1)
            ax.set_xticks(range(0, end_time))
            ax.grid(True, which='both', axis='x', linestyle='--', linewidth=1)

        plt.tight_layout()
        plt.show()
