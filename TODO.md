# Remove Kafka and AWS Components

## Files to Delete
- [x] backend/kafka_client.py
- [x] backend/kafka_producer.py
- [x] backend/kafka_consumer.py
- [x] backend/aws_config.py
- [x] backend/s3_storage.py
- [x] backend/dynamodb_storage.py
- [x] backend/monitoring.py
- [x] terraform/main.tf

## Files to Update
- [x] backend/config.py: Remove Kafka and AWS settings
- [x] backend/app.py: Remove Kafka imports and logic
- [x] backend/requirements.txt: Remove any Kafka/AWS dependencies

## Verification
- [x] Search for 'kafka' to ensure no references remain
- [x] Search for 'aws' to ensure no references remain
