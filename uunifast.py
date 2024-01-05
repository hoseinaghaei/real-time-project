import csv
import random
import math
import binpacking


def generate_uunifast(nsets: int, u: float, n: int, filename: str):
    sets = []
    while len(sets) < nsets:
        utilizations = []
        sumU = u
        for i in range(1, n):
            nextSumU = sumU * random.random() ** (1.0 / (n - i))
            utilizations.append(sumU - nextSumU)
            sumU = nextSumU
        utilizations.append(sumU)

        if all(ut <= 1 for ut in utilizations):
            sets.append(utilizations)

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Task ' + str(i) for i in range(1, n + 1)])
        for utilizations in sets:
            writer.writerow(utilizations)

    return sets


utilizations = generate_uunifast(nsets=1, u=0.7 * 8, n=100, filename='task_utilization.csv')

tasks = []
for utilization in utilizations[0]:
    c = math.ceil(random.uniform(1, 20))
    deadline = c // utilization
    if random.randint(0, 1) == 1:
        tasks.append([c, deadline, "Hard", utilization])
    else:
        tasks.append([c, deadline, "Soft", utilization])

csv_file = 'tasks.csv'

# Write tasks to CSV file
with open(csv_file, 'w', newline='') as file:
    writer = csv.writer(file)

    # Write header
    writer.writerow(["Execution Time", "Deadline", "Criticality", "Utilization"])

    # Write tasks
    writer.writerows(tasks)

print(f'Tasks written to {csv_file}')

b = [i[3] for i in tasks]

bins = binpacking.to_constant_bin_number(b, 8)

for i in bins:
    print(sum(i))
