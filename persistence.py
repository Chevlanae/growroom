import shelve
import tasks
import asyncio


class task_handler:

    def __init__(self, filename):
        self.event_loop = asyncio.get_event_loop()
        self.tasks_set = set()
        self.filename = filename

        # read tasks_db and start stored tasks
        with shelve.open(filename) as tasks_db:
            for key in tasks_db.keys():
                self.start(key, **tasks_db[key])

    def start(self, task_id, **kwargs):

        # create task with provided task_id and keyword arguments
        task = self.event_loop.create_task(getattr(tasks, task_id)(**kwargs))

        # set task id
        task.set_name(task_id)

        # add task to set for a strong reference
        self.tasks_set.add(task)

        # add task info to persistence object
        with shelve.open(self.filename) as tasks_db:
            tasks_db[task_id] = kwargs

        # run event loop if it's stopped
        if not self.event_loop.is_running():
            self.event_loop.run_in_executor(None, self.event_loop.run_forever)

    def stop(self, task_id):

        # stop task and clear it from memory
        for task in self.tasks_set:
            if task.get_name() == task_id:
                task.cancel()
                self.tasks_set.discard(task)
                break

        # remove item from persistence object
        with shelve.open(self.filename) as tasks_db:
            del tasks_db[task_id]

        # stop event loop if there are no running tasks
        if len(self.tasks_set) == 0:
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)
