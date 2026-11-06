import os
import json
import threading
import time
import asyncio
import pika
import redis
from app.core.config import settings
from app.core.logging import logger
from app.services.quality_service import quality_service


class QualityEventConsumer:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._connection: pika.BlockingConnection | None = None
        self._channel = None
        self._redis_client: redis.Redis | None = None

        redis_url = os.getenv("REDIS_URL")
        try:
            if redis_url:
                self._redis_client = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
            else:
                self._redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
            self._redis_client.ping()
            logger.info("Connected to Redis successfully in QualityService.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Fallback to in-memory/MongoDB.")
            self._redis_client = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_consumer, daemon=True, name="RabbitMQQualityConsumer")
        self._thread.start()
        logger.info("QualityService RabbitMQ consumer thread started.")

    def stop(self):
        self._stop_event.set()
        try:
            if self._connection and self._connection.is_open:
                self._connection.close()
        except Exception as e:
            logger.warning(f"Error closing RabbitMQ connection: {e}")
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("QualityService RabbitMQ consumer thread stopped.")

    def _get_connection_parameters(self) -> pika.ConnectionParameters | pika.URLParameters:
        rabbitmq_url = os.getenv("RABBITMQ_URL")
        if rabbitmq_url:
            return pika.URLParameters(rabbitmq_url)

        credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
        return pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=60,
            blocked_connection_timeout=300
        )

    def _run_consumer(self):
        while not self._stop_event.is_set():
            try:
                parameters = self._get_connection_parameters()
                logger.info(f"Connecting to RabbitMQ...")
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()

                exchange_name = settings.RABBITMQ_EXCHANGE
                queue_name = settings.RABBITMQ_QUEUE_QUALITY

                # Declare exchange
                self._channel.exchange_declare(
                    exchange=exchange_name,
                    exchange_type="topic",
                    durable=True
                )

                # Declare durable queue
                self._channel.queue_declare(
                    queue=queue_name,
                    durable=True
                )

                # Bind to post.created and comment.created
                self._channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key="post.created")
                self._channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key="comment.created")

                self._channel.basic_qos(prefetch_count=5)
                self._channel.basic_consume(
                    queue=queue_name,
                    on_message_callback=self._on_message,
                    auto_ack=False
                )

                logger.info(f"RabbitMQ Quality Consumer listening on queue '{queue_name}' bound to '{exchange_name}'")
                self._channel.start_consuming()

            except pika.exceptions.AMQPConnectionError as e:
                if not self._stop_event.is_set():
                    logger.warning(f"RabbitMQ connection failed: {e}. Retrying in 5 seconds...")
                    time.sleep(5)
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"Unexpected error in RabbitMQ Quality consumer: {e}. Retrying in 5 seconds...")
                    time.sleep(5)

    def _on_message(self, ch, method, properties, body):
        try:
            payload = json.loads(body.decode("utf-8"))
            event_type = payload.get("eventType")
            data = payload.get("data", {})
            routing_key = method.routing_key

            logger.info(f"Received event '{event_type}' with routing key '{routing_key}'")

            content = data.get("content", "")
            post_id = data.get("postId")
            comment_id = data.get("commentId")
            content_type = "comment" if "comment" in routing_key else "post"

            if content:
                # Run async analyze_article in new loop for this consumer thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    quality_service.analyze_article(content=content, content_type=content_type)
                )
                loop.close()

                logger.info(
                    f"Analyzed {content_type} (id: {post_id or comment_id}): "
                    f"valid={result.is_valid}, score={result.quality_score}, toxicity={result.toxicity.label}"
                )

                # Cache analysis result in Redis (TTL: 24h)
                entity_id = post_id or comment_id
                if self._redis_client and entity_id:
                    try:
                        cache_key = f"quality:analysis:{entity_id}"
                        self._redis_client.setex(
                            cache_key,
                            86400,
                            json.dumps(result.model_dump())
                        )
                    except Exception as err:
                        logger.warning(f"Failed to cache quality analysis in Redis: {err}")

            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error processing RabbitMQ message: {e}")
            # Acknowledge to prevent poison messages blocking queue
            ch.basic_ack(delivery_tag=method.delivery_tag)


quality_event_consumer = QualityEventConsumer()
