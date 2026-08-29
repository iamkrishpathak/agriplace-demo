from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import asyncio

app = FastAPI(title="AgriPlace API Gateway (BFF)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUTH_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
USER_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
MARKET_URL = os.getenv("MARKETPLACE_SERVICE_URL", "http://marketplace-service:8000")
ORDER_URL = os.getenv("ORDER_SERVICE_URL", "http://order-service:8000")
LOGISTICS_URL = os.getenv("LOGISTICS_SERVICE_URL", "http://logistics-service:8000")
PAYMENT_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")
NOTIFICATION_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")
ML_URL = os.getenv("ML_SERVICE_URL", "http://ml-service:8000")

# Map URL prefixes → upstream service base URLs
SERVICE_ROUTES = {
    "/api/v1/auth": AUTH_URL,
    "/api/v1/users": USER_URL,
    "/api/v1/marketplace": MARKET_URL,
    "/api/v1/orders": ORDER_URL,
    "/api/v1/logistics": LOGISTICS_URL,
    "/api/v1/payments": PAYMENT_URL,
    "/api/v1/notifications": NOTIFICATION_URL,
    "/api/v1/ml": ML_URL,
}

async def forward_request(method: str, url: str, request: Request, json_body=None):
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    async with httpx.AsyncClient() as client:
        try:
            req = client.build_request(
                method, 
                url, 
                headers=headers,
                json=json_body,
                params=request.query_params
            )
            response = await client.send(req)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Bad Gateway: {str(e)}")

def api_response(data=None, error=None, success=True):
    return {"success": success, "data": data, "error": error}

@app.get("/health")
def health():
    return {"success": True, "data": {"status": "ok"}}

@app.post("/auth/login")
async def login(request: Request):
    body = await request.json()
    res = await forward_request("POST", f"{AUTH_URL}/api/v1/auth/login", request, body)
    return JSONResponse(status_code=200 if res.get("success") else 400, content=res)

@app.get("/farmer/home")
async def farmer_home(request: Request):
    # Aggregate data for farmer dashboard
    lang = request.query_params.get("lang", "en")
    
    async with httpx.AsyncClient() as client:
        # We need headers for auth
        headers = {"Authorization": request.headers.get("Authorization", "")}
        
        # In a real app we'd fetch actual listings and orders. For prototype, we'll return mock structure matching frontend
        # Because we didn't implement the exact complex queries in microservices yet
        data = {
            "text": {
                "greeting": "नमस्ते" if lang == "hi" else "Hello",
                "sell_button": "फसल बेचें" if lang == "hi" else "Sell Crop",
                "market_label": "आज टमाटर का भाव" if lang == "hi" else "Today's tomato mandi price",
                "earning_label": "अनुमानित बिक्री" if lang == "hi" else "Expected sale value",
            },
            "market_price": {"range_per_kg": [22, 28]},
            "expected_earnings": 12500,
            "active_listings": [],
            "orders": [],
            "alerts": []
        }
        
        try:
            listings_res = await client.get(f"{MARKET_URL}/api/v1/marketplace/listings", headers=headers)
            if listings_res.status_code == 200:
                # Map to frontend format
                raw_listings = listings_res.json().get("data", [])
                data["active_listings"] = [{
                    "id": l["id"],
                    "crop": {"name": "Tomato"},
                    "quantity_kg": l["quantity_kg"],
                    "grade": l["grade"],
                    "expected_price_per_kg": l["expected_price_per_kg"],
                    "available_date": l["available_date"],
                    "location": {"district": "Nashik"},
                    "farmer": {"name": "Demo Farmer"}
                } for l in raw_listings]
        except:
            pass

    return api_response(data)

@app.get("/buyer/marketplace")
async def buyer_marketplace(request: Request):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": request.headers.get("Authorization", "")}
        try:
            listings_res = await client.get(f"{MARKET_URL}/api/v1/marketplace/listings", headers=headers)
            raw_listings = listings_res.json().get("data", []) if listings_res.status_code == 200 else []
            listings = [{
                "id": l["id"],
                "crop": {"name": "Tomato"},
                "quantity_kg": l["quantity_kg"],
                "grade": l["grade"],
                "expected_price_per_kg": l["expected_price_per_kg"],
                "available_date": l["available_date"],
                "location": {"district": "Nashik"},
                "farmer": {"name": "Demo Farmer"},
                "status": l["status"]
            } for l in raw_listings]
            
            return api_response({
                "filters": ["crop", "quality", "quantity"],
                "listings": listings
            })
        except Exception as e:
            return api_response({"listings": []})

@app.get("/buyer/orders")
async def buyer_orders(request: Request):
    return api_response([]) # Return empty for demo to prevent frontend crash if format differs

@app.get("/buyer/requirements")
async def buyer_requirements(request: Request):
    return api_response([]) 

@app.get("/transporter/active")
async def transporter_active(request: Request):
    return api_response(None)

@app.get("/transporter/trips/available")
async def transporter_available(request: Request):
    return api_response([])

@app.get("/admin/dashboard")
async def admin_dashboard(request: Request):
    return api_response({
        "kpis": {"total_farmers": 142, "active_orders": 12, "total_produce_kg": 45000, "total_transaction_value": 1250000, "route_savings_km": 420},
        "ai_dashboard": {
            "price_forecast": {"predicted_range_per_kg": {"min": 24, "max": 29}},
            "demand_forecast": {"demand_level": "HIGH"},
            "glut_alerts": []
        },
        "system_health": {"api": "Online", "database": "Online"}
    })

@app.get("/admin/matching-weights")
async def admin_weights(request: Request):
    return api_response({"distance": 0.3, "price": 0.4, "quality": 0.3})

@app.get("/admin/audit-logs")
async def admin_audit(request: Request):
    return api_response([])

# Smart prefix-based reverse proxy catch-all
# Any /api/v1/* route not explicitly handled above is forwarded to the correct microservice.
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
async def catch_all(path: str, request: Request):
    full_path = f"/{path}"

    # Match the longest prefix first
    upstream_base = None
    for prefix, base_url in sorted(SERVICE_ROUTES.items(), key=lambda x: -len(x[0])):
        if full_path.startswith(prefix):
            upstream_base = base_url
            break

    if not upstream_base:
        return JSONResponse(
            status_code=404,
            content=api_response(None, f"No upstream service for route: {full_path}", False)
        )

    upstream_url = f"{upstream_base}{full_path}"
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    try:
        body = await request.body()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=upstream_url,
                headers=headers,
                content=body,
                params=request.query_params,
            )
        return JSONResponse(status_code=response.status_code, content=response.json())
    except Exception as e:
        return JSONResponse(
            status_code=502,
            content=api_response(None, f"Bad Gateway: {str(e)}", False)
        )
