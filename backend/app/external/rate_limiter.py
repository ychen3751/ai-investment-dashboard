import asyncio
import time
from collections import defaultdict


class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    async def wait(self):
        while not await self.acquire():
            await asyncio.sleep(0.1)


rate_limiters: dict = defaultdict(lambda: TokenBucket(rate=2, capacity=5))


def get_rate_limiter(name: str = "default") -> TokenBucket:
    return rate_limiters[name]
