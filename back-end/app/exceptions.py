class UnableToFetchResultError(Exception):
    """ Custom exception raised when a result cannot be fetched from the queue. """
    pass


class InvalidTaskName(Exception):
    """ Exception raised when the task name is invalid. """
    pass


class UnableToPublishTask(Exception):
    """ Custom exception raised when a task cannot be published to the queue. """
    pass
