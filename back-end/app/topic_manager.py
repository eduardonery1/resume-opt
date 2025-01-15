import heapq
from asyncio.queues import Queue


class TopicManager:
    MAX_TOPICS = 10_000

    def __init__(self, ):
        self.topic_to_future = {}
        self.topic_to_queue = {}
        self.heap = list()

        self.load_topics()

    def load_topics(self):
        pass

    def get_topic(self):
         

    def get(self, topic):
        if topic not in self.topic_to_queue:
            return None
        return self.topic_to_queue[topic].get_nowait()
