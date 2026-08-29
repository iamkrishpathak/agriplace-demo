import httpx
import asyncio

API_BASE = "http://localhost:8000"

# The gateway proxies /api/v1/{service}/* to the right service.
# Each service's health endpoint is at /health on the service itself,
# which maps to /api/v1/{service}/health... but only if services serve at that path.
# Instead we check the gateway's own health + ping each service via its API prefix.
async def test_health():
    checks = [
        ("/health", "API Gateway"),
        ("/api/v1/auth/health", "Auth Service"),
        ("/api/v1/users/health", "User Service"),
        ("/api/v1/marketplace/health", "Marketplace Service"),
        ("/api/v1/orders/health", "Order Service"),
        ("/api/v1/logistics/health", "Logistics Service"),
        ("/api/v1/payments/health", "Payment Service"),
        ("/api/v1/notifications/health", "Notification Service"),
        ("/api/v1/ml/health", "ML Service"),
    ]

    async with httpx.AsyncClient(timeout=10.0) as client:
        for path, name in checks:
            try:
                res = await client.get(f"{API_BASE}{path}")
                body = res.json()
                if res.status_code == 200:
                    print(f"✅ {name}: OK")
                else:
                    print(f"❌ {name}: FAILED ({res.status_code}) — {body}")
            except Exception as e:
                print(f"❌ {name}: FAILED — {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_health())
