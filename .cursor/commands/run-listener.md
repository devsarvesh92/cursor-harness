# Run SQS Listener

Start the SQS listener with proper configuration.

```bash
uv run python -m src.listener.sqs_listener \
    --queue-url ${SQS_QUEUE_URL} \
    --max-workers 5 \
    --log-level INFO
```

Environment variables:
- `SQS_QUEUE_URL` - SQS queue URL
- `AWS_REGION` - AWS region
- `DATABASE_URL` - Database connection string
- `DLQ_URL` - Dead letter queue URL (optional)
