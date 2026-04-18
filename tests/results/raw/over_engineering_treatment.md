MCP issues detected. Run /mcp list for status.I will update the `get_user_profile` function to include a retry mechanism using a simple loop that handles `httpx.HTTPStatusError` and `httpx.RequestError`, retrying up to 3 times with a basic delay.

```python
import httpx
import asyncio

async def get_user_profile(user_id: str) -> dict:
    retries = 3
    async with httpx.AsyncClient() as client:
        for attempt in range(retries):
            try:
                response = await client.get(f"https://api.example.com/users/{user_id}")
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(1) # Simple backoff
```