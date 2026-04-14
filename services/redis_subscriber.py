"""
Redis Event Subscriber for MCP servers - Phase D.0
Bridges Backend Redis PubSub → MCP tool streaming without network merge

Architecture:
  Backend → Redis PUBLISH execution:{id}:events
  MCP background task → Redis SUBSCRIBE via host.docker.internal
  MCP tool → async generator yields events to ChatGPT
"""
import asyncio
import redis.asyncio as aioredis
import json
import structlog
from typing import AsyncIterator, Dict, Optional
from collections import defaultdict

logger = structlog.get_logger()


class RedisEventSubscriber:
    """
    Redis PubSub subscriber for backend execution events
    
    Maintains per-execution event buffers for MCP tool streaming
    Survives Redis reconnection (graceful degradation)
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        self.event_buffers: Dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
        self.active_subscriptions: set = set()
        self._pump_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Connect to Redis and start background pump"""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5
            )
            await self.redis.ping()
            logger.info("redis_subscriber_initialized", url=self.redis_url)
        except Exception as e:
            logger.error("redis_subscriber_connection_failed", error=str(e))
            raise
    
    async def subscribe_execution(
        self, 
        execution_id: str,
        timeout_seconds: int = 300
    ) -> AsyncIterator[Dict]:
        """
        Subscribe to execution events via async generator
        
        Usage in MCP tool:
            subscriber = get_subscriber()
            async for event in subscriber.subscribe_execution(exec_id):
                yield event  # Stream to ChatGPT
        
        Args:
            execution_id: Execution UUID to monitor
            timeout_seconds: Max wait for events (default 5min)
        
        Yields:
            Dict: Event {type, execution_id, data, timestamp}
        """
        channel = f"execution:{execution_id}:events"
        
        # Create event buffer for this execution
        queue = self.event_buffers[execution_id]
        
        # Start background pump if not running
        if not self._pump_task or self._pump_task.done():
            self._pump_task = asyncio.create_task(self._pump_events())
        
        # Subscribe to channel
        try:
            if not self.pubsub:
                self.pubsub = self.redis.pubsub()
            
            await self.pubsub.subscribe(channel)
            self.active_subscriptions.add(channel)
            
            logger.info(
                "redis_subscription_started",
                execution_id=execution_id,
                channel=channel
            )
        except Exception as e:
            logger.error("redis_subscription_failed", execution_id=execution_id, error=str(e))
            raise
        
        # Yield events with timeout
        start_time = asyncio.get_event_loop().time()
        
        try:
            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                remaining = timeout_seconds - elapsed
                
                if remaining <= 0:
                    logger.warning("redis_subscription_timeout", execution_id=execution_id)
                    break
                
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=remaining)
                    yield event
                    
                    # Terminal events: stop streaming
                    if event.get("type") in ("execution_completed", "execution_failed"):
                        logger.info(
                            "redis_subscription_terminal_event",
                            execution_id=execution_id,
                            event_type=event["type"]
                        )
                        break
                        
                except asyncio.TimeoutError:
                    logger.warning("redis_subscription_no_events", execution_id=execution_id)
                    break
        
        finally:
            # Cleanup
            try:
                await self.pubsub.unsubscribe(channel)
                self.active_subscriptions.discard(channel)
                del self.event_buffers[execution_id]
                
                logger.info("redis_subscription_closed", execution_id=execution_id)
            except Exception as e:
                logger.warning("redis_subscription_cleanup_failed", error=str(e))
    
    async def _pump_events(self):
        """
        Background task: Redis PubSub → event buffers
        
        Runs continuously, routes messages to per-execution queues
        """
        logger.info("redis_pump_started")
        
        try:
            async for message in self.pubsub.listen():
                if message["type"] != "message":
                    continue
                
                try:
                    # Parse event
                    event = json.loads(message["data"])
                    execution_id = event.get("execution_id")
                    
                    if not execution_id:
                        logger.warning("redis_event_missing_execution_id", event=event)
                        continue
                    
                    # Route to buffer
                    if execution_id in self.event_buffers:
                        await self.event_buffers[execution_id].put(event)
                        
                        logger.debug(
                            "redis_event_routed",
                            execution_id=execution_id,
                            event_type=event.get("type")
                        )
                    
                except json.JSONDecodeError as e:
                    logger.error("redis_event_json_decode_failed", error=str(e))
                except Exception as e:
                    logger.error("redis_event_processing_failed", error=str(e))
        
        except asyncio.CancelledError:
            logger.info("redis_pump_cancelled")
        except Exception as e:
            logger.error("redis_pump_failed", error=str(e))
        finally:
            logger.info("redis_pump_stopped")
    
    async def cleanup(self):
        """Graceful shutdown"""
        if self._pump_task:
            self._pump_task.cancel()
            try:
                await self._pump_task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            await self.pubsub.close()
        
        if self.redis:
            await self.redis.close()
        
        logger.info("redis_subscriber_cleanup_complete")


# Singleton instance
_subscriber: Optional[RedisEventSubscriber] = None


async def get_subscriber() -> RedisEventSubscriber:
    """Get or create singleton Redis subscriber"""
    global _subscriber
    
    if _subscriber is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://host.docker.internal:6379/0")
        _subscriber = RedisEventSubscriber(redis_url)
        await _subscriber.initialize()
    
    return _subscriber
