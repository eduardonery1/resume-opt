import unittest
from ..queue_publishers import GooglePubSubPublisher
from unittest.mock import patch, MagicMock


class TestGooglePubSubPublisher(unittest.TestCase):
    @patch('google.cloud.pubsub_v1.PublisherClient')
    def test_publish(self, mock_publisher_client):
        # Setup
        channel = "my-topic"
        project = "my-project"
        publisher = GooglePubSubPublisher(channel, project)
        message = "Hello, world!"
        expected_topic_name = f"projects/{project}/topics/{channel}"
        expected_message_bytes = message.encode('utf-8')

        # Mock the publisher's publish method
        mock_publisher = MagicMock()
        mock_publisher_client.return_value = mock_publisher
        mock_future = MagicMock()
        mock_publisher.publish.return_value = mock_future

        # Execute
        publisher.publish(message)

        # Assert
        mock_publisher.publish.assert_called_once_with(expected_topic_name, data=expected_message_bytes)


if __name__ == '__main__':
    unittest.main()
