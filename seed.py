import httpx
import asyncio
import time

API_BASE = "http://localhost:8000/api/v1"

async def wait_for_api():
    print("Waiting for API Gateway to be healthy...")
    async with httpx.AsyncClient() as client:
        for _ in range(60):
            try:
                res = await client.get("http://localhost:8000/health")
                if res.status_code == 200:
                    print("API Gateway is up!")
                    return
            except:
                pass
            time.sleep(2)
    raise Exception("API Gateway did not become healthy in time.")

async def seed():
    await wait_for_api()
    async with httpx.AsyncClient() as client:
        print("Registering Farmer...")
        res = await client.post(f"{API_BASE}/auth/register", json={
            "name": "Demo Farmer",
            "email": "farmer@agriplace.demo",
            "password": "AgriPlace@123",
            "role": "FARMER"
        })
        farmer_data = res.json()
        print(farmer_data)
        
        print("Registering Buyer...")
        res = await client.post(f"{API_BASE}/auth/register", json={
            "name": "Demo Buyer",
            "email": "buyer@agriplace.demo",
            "password": "AgriPlace@123",
            "role": "BUYER"
        })
        print(res.json())

        print("Registering Transporter...")
        res = await client.post(f"{API_BASE}/auth/register", json={
            "name": "Demo Transporter",
            "email": "transporter@agriplace.demo",
            "password": "AgriPlace@123",
            "role": "TRANSPORTER"
        })
        print(res.json())

        # Note: In a complete seed we would login, get JWT, and call profile creation, marketplace listings etc.
        # This script just creates the core accounts needed to log into the frontend.

if __name__ == "__main__":
    asyncio.run(seed())
