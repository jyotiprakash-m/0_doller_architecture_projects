from confluent_kafka import Consumer, Producer
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_DOCUMENT_INDEXING

print(f"Testing Kafka on {KAFKA_BOOTSTRAP_SERVERS}")
c = Consumer({
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'test_group',
    'auto.offset.reset': 'earliest'
})
c.subscribe([KAFKA_TOPIC_DOCUMENT_INDEXING])
msg = c.poll(5.0)
if msg is None:
    print("No message received.")
elif msg.error():
    print("Error:", msg.error())
else:
    print("Message received:", msg.value().decode('utf-8'))
c.close()
