import logging
import os
import boto3

from botocore.exceptions import ClientError

from insights_messaging.consumers import Consumer

log = logging.getLogger(__name__)

class SQS(Consumer):
    def __init__(
        self,
        publisher,
        downloader,
        engine,
        redis,
        aws_access_key_env,
        aws_secret_access_key_env,
        queue,
        **kwargs
    ):

        super().__init__(publisher, downloader, engine, redis)

        aws_access_key_id = os.getenv(aws_access_key_env, "AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv(aws_secret_access_key_env, "AWS_SECRET_ACCESS_KEY")
        
        self.client = boto3.client("sqs",
                                   aws_access_key_id=aws_access_key_id,
                                   aws_secret_access_key=aws_secret_access_key)
        self.queue = queue
        self.delete_message = kwargs.get("delete_message")
        
    
    def get_queue_url(self):
        return self.client.get_queue_url(QueueName=self.queue)

    def deserialize(self, bytes_):
        raise NotImplementedError()

    def handles(self, input_msg):
        return True

    def run(self):
        queue_url = self.get_queue_url()
        
        while True:
            try:
                messages = self.client.receive_message(QueueUrl=queue_url["QueueUrl"])
                if messages["Messages"] == []:
                    continue
            except ClientError as e:
                log.exception(e)
                continue
            
            for message in messages["Messages"]:
                try:
                    if self.handles(message):
                        self.process(message)
                except Exception as ex:
                    log.exception(ex)
                finally:
                    if self.delete_message:
                        self.client.delete(QueueUrl=queue_url,
                                           ReceiptHandle=message["ReceiptHandle"])
