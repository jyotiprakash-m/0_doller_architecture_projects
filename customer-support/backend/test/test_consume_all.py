from confluent_kafka import Consumer
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_DOCUMENT_INDEXING

c = Consumer({
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'test_group_all_2',
    'auto.offset.reset': 'earliest'
})
c.subscribe([KAFKA_TOPIC_DOCUMENT_INDEXING])
count = 0
empty_polls = 0
while True:
    msg = c.poll(1.0)
    if msg is None:
        empty_polls += 1
        if empty_polls > 10:  # wait 10 seconds total
            break
        continue
    empty_polls = 0
    if msg.error():
        continue
    count += 1
    print(f"Msg {count}: {msg.value().decode('utf-8')}")
c.close()
print(f"Total messages: {count}")
