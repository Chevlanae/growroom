import shelve
import tasks
import asyncio


class task_handler:
    '''High-level class to dynamically schedule and manage coroutines defined in "./tasks.py" with a built-in event loop. 
    Tasks are persistent and __init__ will attempt to reschedule any coroutines that were running if  the application was stopped.'''

    def __init__(self, filename, persistence=True):

        self.event_loop = asyncio.get_event_loop()
        self.tasks = set()
        self.filename = filename

        if persistence:

            # read tasks_db and start stored tasks
            with shelve.open(filename) as tasks_db:
                for id in tasks_db.keys():
                    task_info = tasks_db[id]
                    self.start(task_info["coro"], id, **task_info["kwargs"])

    def start(self, coro, task_id, **kwargs):
        '''Schedules and runs a coroutine defined in "./tasks.py" who's name matches the given "task_id". 
        Keyword arguments have to be basic data types, or anything pickle-able.'''

        # create task with provided task_id and keyword arguments
        task = self.event_loop.create_task(
            getattr(tasks, coro)(**kwargs), name=task_id)

        # add task to set for future reference, and to prevent garbage collection
        self.tasks.add(task)

        # add task info to persistence object
        with shelve.open(self.filename) as tasks_db:
            tasks_db[task_id] = {
                "coro": coro,
                "kwargs": kwargs
            }

        # run event loop if it's stopped
        if not self.event_loop.is_running():
            self.event_loop.run_in_executor(None, self.event_loop.run_forever)

    def stop(self, task_id):
        '''Calls Task.cancel() on a running task who's Task.get_name() matches the given "task_id"'''

        # stop task and clear it from memory
        if task_id in self.list_tasks():

            task = self.fetch_task(task_id)

            task.cancel()
            self.tasks.discard(task)

        # remove item from persistence object
        with shelve.open(self.filename) as tasks_db:
            del tasks_db[task_id]

        # stop event loop if there are no running tasks
        if len(self.tasks) == 0:
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)

    def fetch_task(self, task_id):
        '''Returns a Task object where Task.get_name() matches the given "task_id", else returns None'''

        query = None

        # binary search for a task who's name matches "task_id"
        for task in self.tasks:
            if task.get_name() == task_id:
                query = task
                break

        return query

    def fetch_task_info(self, task_id):
        with shelve.open(self.filename) as tasks_db:
            try:
                info = tasks_db[task_id]
            except KeyError:
                info = None

            return info

    def list_tasks(self):
        '''List the result of Task.get_name() for every element in self.tasks'''

        # generate array of task names
        arr = []
        for task in self.tasks:
            arr.append(task.get_name())

        return arr
