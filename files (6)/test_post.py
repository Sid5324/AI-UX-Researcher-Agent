import httpx
import asyncio
import json

async def test():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "http://localhost:8000/goals",
                json={"description": "Test research goal", "mode": "demo"},
                timeout=30.0
            )
            print(f"Status: {resp.status_code}")
            print(f"Body: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
