import asyncio, aioredis, os, sys
import constants

async def check():
    try:
        redis = await aioredis.from_url(constants.REDIS_URL)
        pong = await redis.ping()
        if pong:
            print("Redis OK")
            return 0
        return 1
    except Exception as e:
        print(f"Healthcheck failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(check()))