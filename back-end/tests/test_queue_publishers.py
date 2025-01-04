import unittest
from app.queue_publishers import GooglePubSubPublisher
from unittest.mock import patch, MagicMock, Mock


class TestGooglePubSubPublisher(unittest.TestCase):
    @patch('app.queue_publishers.PublisherClient')
    def test_publish(self, mock_publisher_client):
        # Mock the publisher's publish method
        mock_future = MagicMock()
        mock_future.result.return_value = None
        mock_instance = mock_publisher_client.return_value = MagicMock()
        mock_instance.publish.return_value = mock_future

        # Setup
        channel = "my-topic"
        project = "my-project"
        publisher = GooglePubSubPublisher(channel, project)

        # Execute
        message = "Hello, world!"
        publisher.publish(message)

        # Assert
        expected_topic_name = f"projects/{project}/topics/{channel}"
        expected_message_bytes = message.encode('utf-8')
        mock_instance.publish.assert_called_once_with(
                topic=expected_topic_name, 
                data=expected_message_bytes
                )


if __name__ == '__main__':
    unittest.main()
