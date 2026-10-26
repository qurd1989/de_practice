import queue


def task(name, work_queue):
    if work_queue.empty():
        print(f"{name} has no more work to do.")
        return

    while not work_queue.empty():
        count = work_queue.get()
        total = 0
        print(f"{name} is processing task {count}.")
        for _ in range(count):
            total += 1
        print(f"{name} completed task {count} with total {total}.")


def main():
    """
    This is the main entry point for program.
    """
    work_queue = queue.Queue()

    # Add some tasks to the queue.
    for i in range(5):
        work_queue.put(i)

    # Create some synchronous tasks.
    tasks = [
        (task, "One", work_queue),
        (task, "Two", work_queue),
        (task, "Three", work_queue),
    ]

    # Run the tasks sequentially.
    for func, name, q in tasks:
        func(name, q)


if __name__ == "__main__":
    main()