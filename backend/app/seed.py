from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.models import (
    Alert,
    BuyerProfile,
    BuyerRequirement,
    CollectionCenter,
    Crop,
    CropVariety,
    DataClass,
    FarmerProfile,
    FPOProfile,
    Grade,
    Location,
    MarketArrival,
    MarketPrice,
    Notification,
    ReputationScore,
    Role,
    RoleName,
    StateRule,
    TransporterProfile,
    User,
    Vehicle,
)
from backend.app.services.audit import audit
from backend.app.services.workflows import create_protected_order_from_requirement


DEMO_PASSWORD = "AgriPlace@123"


def _user(db: Session, name: str, email: str, role: RoleName, phone: str, lang: str = "en") -> User:
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        return existing
    user = User(
        name=name,
        email=email,
        phone=phone,
        password_hash=hash_password(DEMO_PASSWORD),
        preferred_language=lang,
    )
    db.add(user)
    db.flush()
    db.add(Role(user_id=user.id, name=role))
    db.flush()
    return user


def _location(
    db: Session,
    label: str,
    address: str,
    district: str,
    state: str,
    latitude: float,
    longitude: float,
    location_type: str,
) -> Location:
    existing = db.scalar(select(Location).where(Location.label == label))
    if existing:
        return existing
    location = Location(
        label=label,
        address=address,
        district=district,
        state=state,
        latitude=latitude,
        longitude=longitude,
        location_type=location_type,
        data_classification=DataClass.SYNTHETIC,
    )
    db.add(location)
    db.flush()
    return location


def _crop(db: Session, name: str, hindi_name: str, perishability: str) -> Crop:
    existing = db.scalar(select(Crop).where(Crop.name == name))
    if existing:
        return existing
    crop = Crop(name=name, hindi_name=hindi_name, perishability=perishability)
    db.add(crop)
    db.flush()
    return crop


def seed_db(db: Session) -> None:
    if db.scalar(select(User).where(User.email == "farmer@agriplace.demo")):
        return

    tomato = _crop(db, "Tomato", "टमाटर", "HIGH")
    onion = _crop(db, "Onion", "प्याज", "MEDIUM")
    potato = _crop(db, "Potato", "आलू", "MEDIUM")
    wheat = _crop(db, "Wheat", "गेहूं", "LOW")
    for crop, variety in [(tomato, "Hybrid"), (tomato, "Desi"), (onion, "Red"), (potato, "Jyoti"), (wheat, "Lokwan")]:
        db.add(CropVariety(crop_id=crop.id, name=variety))

    depot = _location(
        db,
        "AgriPlace Nashik Pooling Depot",
        "Near Mumbai-Agra highway, Nashik logistics pooling point",
        "Nashik",
        "Maharashtra",
        19.9975,
        73.7898,
        "DEPOT",
    )
    ramesh_farm = _location(
        db,
        "Ramesh Farm, Pimpalgaon",
        "Pimpalgaon Baswant, Nashik",
        "Nashik",
        "Maharashtra",
        20.1662,
        73.9878,
        "FARM",
    )
    kavita_farm = _location(
        db,
        "Kavita Farm, Dindori",
        "Dindori Road, Nashik",
        "Nashik",
        "Maharashtra",
        20.2005,
        73.8272,
        "FARM",
    )
    fpo_center_location = _location(
        db,
        "Sahyadri FPO Collection Center",
        "Mohadi village collection center, Nashik",
        "Nashik",
        "Maharashtra",
        20.0893,
        73.8621,
        "COLLECTION_CENTER",
    )
    buyer_location = _location(
        db,
        "Mumbai FreshMart Warehouse",
        "Vashi APMC logistics gate, Navi Mumbai",
        "Mumbai",
        "Maharashtra",
        19.0771,
        72.9989,
        "BUYER_WAREHOUSE",
    )

    fpo = FPOProfile(
        name="Sahyadri Tomato Growers FPO",
        registration_number="FPO-MH-NAS-2026-01",
        district="Nashik",
        state="Maharashtra",
    )
    db.add(fpo)
    db.flush()
    db.add(
        CollectionCenter(
            name="Sahyadri FPO Quality & Pooling Hub",
            center_type="FPO collection center",
            location_id=fpo_center_location.id,
            capacity_kg=12000,
            operating_hours="06:00-18:00",
            services=["quality inspection", "weighing", "aggregation", "short-term storage"],
        )
    )

    farmer = _user(db, "Ramesh Patil", "farmer@agriplace.demo", RoleName.FARMER, "+919810000001", "hi")
    farmer_b = _user(db, "Kavita Shinde", "farmer2@agriplace.demo", RoleName.FARMER, "+919810000002", "hi")
    fpo_user = _user(db, "Sahyadri FPO Desk", "fpo@agriplace.demo", RoleName.FARMER, "+919810000003", "en")
    buyer = _user(db, "Anaya Rao", "buyer@agriplace.demo", RoleName.BUYER, "+919810000010", "en")
    transporter = _user(
        db, "Imran Shaikh", "transporter@agriplace.demo", RoleName.TRANSPORTER, "+919810000020", "en"
    )
    admin = _user(db, "Admin Console", "admin@agriplace.demo", RoleName.ADMIN, "+919810000099", "en")

    db.add_all(
        [
            FarmerProfile(
                user_id=farmer.id,
                village="Pimpalgaon",
                district="Nashik",
                state="Maharashtra",
                land_acres=2.4,
                fpo_id=fpo.id,
            ),
            FarmerProfile(
                user_id=farmer_b.id,
                village="Dindori",
                district="Nashik",
                state="Maharashtra",
                land_acres=3.1,
                fpo_id=fpo.id,
            ),
            FarmerProfile(
                user_id=fpo_user.id,
                village="Mohadi",
                district="Nashik",
                state="Maharashtra",
                land_acres=18.0,
                fpo_id=fpo.id,
            ),
            BuyerProfile(
                user_id=buyer.id,
                buyer_type="Bulk Retailer",
                business_name="Mumbai FreshMart",
                gstin="27ABCDE1234F1Z5",
            ),
            TransporterProfile(
                user_id=transporter.id,
                company_name="Nashik Roadlink Logistics",
                license_number="MH-TRANS-88210",
            ),
        ]
    )
    db.flush()
    profile = db.scalar(select(TransporterProfile).where(TransporterProfile.user_id == transporter.id))
    db.add_all(
        [
            Vehicle(
                transporter_id=profile.id,
                registration_number="MH15 TR 2048",
                vehicle_type="Mini Truck",
                capacity_kg=2000,
                cold_chain=False,
            ),
            Vehicle(
                transporter_id=profile.id,
                registration_number="MH15 CC 1209",
                vehicle_type="Refrigerated Van",
                capacity_kg=1200,
                cold_chain=True,
            ),
        ]
    )

    today = date.today()
    for market, min_price, max_price, modal_price in [
        ("Nashik", 2350, 2800, 2580),
        ("Pimpalgaon", 2400, 2850, 2620),
        ("Mumbai", 2650, 3180, 2920),
    ]:
        db.add(
            MarketPrice(
                crop_id=tomato.id,
                state="Maharashtra",
                district="Nashik" if market != "Mumbai" else "Mumbai",
                market=market,
                variety="Hybrid",
                grade="FAQ",
                arrival_date=today - timedelta(days=1),
                min_price=min_price,
                max_price=max_price,
                modal_price=modal_price,
                source="Schema-compatible sample for data.gov.in Current Daily Price of Various Commodities from Various Markets (Mandi)",
                data_classification=DataClass.SYNTHETIC,
            )
        )
    for days_ago, tonnes in [(1, 1260), (2, 1180), (3, 1100), (4, 980), (5, 930)]:
        db.add(
            MarketArrival(
                crop_id=tomato.id,
                market="Nashik",
                arrival_date=today - timedelta(days=days_ago),
                arrival_quantity_tonnes=tonnes,
                source="Agmarknet-style arrivals proxy sample for MVP",
            )
        )

    from backend.app.models import ProduceListing

    db.add_all(
        [
            ProduceListing(
                farmer_id=farmer.id,
                fpo_id=fpo.id,
                crop_id=tomato.id,
                location_id=ramesh_farm.id,
                quantity_kg=1000,
                available_date=today + timedelta(days=1),
                grade=Grade.A,
                expected_price_per_kg=26,
                image_url="/demo/tomato-a.jpg",
                max_transit_hours=10,
                storage_requirement="Shade, ventilated crates",
                temperature_requirement="Ambient, avoid direct sun",
            ),
            ProduceListing(
                farmer_id=farmer_b.id,
                fpo_id=fpo.id,
                crop_id=tomato.id,
                location_id=kavita_farm.id,
                quantity_kg=600,
                available_date=today + timedelta(days=1),
                grade=Grade.A,
                expected_price_per_kg=25.5,
                image_url="/demo/tomato-b.jpg",
            ),
            ProduceListing(
                farmer_id=fpo_user.id,
                fpo_id=fpo.id,
                crop_id=tomato.id,
                location_id=fpo_center_location.id,
                quantity_kg=400,
                available_date=today + timedelta(days=1),
                grade=Grade.A,
                expected_price_per_kg=25.8,
                image_url="/demo/tomato-fpo.jpg",
            ),
        ]
    )
    db.add_all(
        [
            ReputationScore(
                user_id=farmer.id,
                role=RoleName.FARMER,
                score=92,
                components={"fulfillment": 96, "quality_consistency": 91, "on_time_readiness": 90},
            ),
            ReputationScore(
                user_id=farmer_b.id,
                role=RoleName.FARMER,
                score=89,
                components={"fulfillment": 92, "quality_consistency": 88, "on_time_readiness": 87},
            ),
            ReputationScore(
                user_id=fpo_user.id,
                role=RoleName.FARMER,
                score=94,
                components={"fulfillment": 97, "quality_consistency": 93, "on_time_readiness": 92},
            ),
            ReputationScore(
                user_id=buyer.id,
                role=RoleName.BUYER,
                score=91,
                components={"payment_reliability": 98, "cancellation_rate": 5, "dispute_rate": 3},
            ),
            ReputationScore(
                user_id=transporter.id,
                role=RoleName.TRANSPORTER,
                score=88,
                components={"on_time_delivery": 89, "pickup_reliability": 93, "incident_rate": 4},
            ),
        ]
    )

    req = BuyerRequirement(
        buyer_id=buyer.id,
        crop_id=tomato.id,
        destination_location_id=buyer_location.id,
        required_quantity_kg=2000,
        grade=Grade.A,
        needed_by=today + timedelta(days=3),
        max_price_per_kg=30,
    )
    db.add(req)
    db.flush()

    db.add_all(
        [
            Alert(
                user_id=farmer.id,
                crop_id=tomato.id,
                alert_type="SUPPLY_GLUT",
                severity="warning",
                title="Possible tomato supply glut",
                message="Tomato arrivals may increase over the next 5 days. This is a forecast, not a certainty.",
            ),
            Notification(
                user_id=farmer.id,
                notification_type="PRICE_ALERT",
                title="आज टमाटर का भाव अच्छा है",
                message="अनुमानित बाजार भाव 24-29 रुपये/kg है।",
            ),
            Notification(
                user_id=buyer.id,
                notification_type="MATCH_READY",
                title="2,000 kg tomato match ready",
                message="Three verified sellers can fulfill your requirement.",
            ),
            Notification(
                user_id=transporter.id,
                notification_type="NEW_TRIP",
                title="New pooled Nashik to Mumbai trip",
                message="2,000 kg tomatoes, optimized route available.",
            ),
        ]
    )
    db.add(
        StateRule(
            state="Maharashtra",
            market_type="APMC/direct-trade configurable demo",
            mandi_requirements="Verify state-specific market rules before production operations.",
            direct_sale_allowed=True,
            documentation_requirements=["invoice", "weighing slip", "quality note", "transport challan"],
            special_rules="Prototype rule only; not legal advice or universal compliance.",
        )
    )

    db.add_all(
        [
            _data_source(
                "Daily mandi commodity prices",
                "Ministry of Agriculture & Farmers Welfare / Directorate of Marketing & Inspection",
                "https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi",
                "REST API with data.gov.in API key",
                "JSON/CSV/XML",
                ["state", "district", "market", "commodity", "variety", "grade", "arrival_date", "min_price", "max_price", "modal_price"],
                "India, mandi level",
                "Current daily endpoint; historical via Agmarknet extraction",
                "Daily",
                "Government Open Data License - India",
                True,
                "Public mandi prices do not represent private farmer transaction prices; arrival quantity may require Agmarknet feed.",
            ),
            _data_source(
                "OpenStreetMap road network",
                "OpenStreetMap contributors",
                "https://www.openstreetmap.org/copyright",
                "OSM extracts, OSRM/OpenRouteService routing APIs",
                "PBF/GeoJSON/API JSON",
                ["coordinates", "ways", "road classes", "route geometry"],
                "Global",
                "Continuously updated community map",
                "Continuous",
                "Open Database License",
                True,
                "Requires attribution and usage-policy compliant routing/geocoding providers.",
            ),
            _data_source(
                "Open-Meteo historical weather",
                "Open-Meteo using ERA5/ERA5-Land reanalysis",
                "https://open-meteo.com/en/docs/historical-weather-api",
                "REST API",
                "JSON/CSV/XLSX",
                ["temperature_2m", "relative_humidity_2m", "precipitation", "soil_moisture", "solar_radiation"],
                "Global coordinates",
                "1940-present depending on model",
                "Daily / model-dependent",
                "CC BY 4.0; commercial usage subject to terms",
                True,
                "Reanalysis data is modeled, not direct station measurement for every farm.",
            ),
        ]
    )
    db.flush()

    create_protected_order_from_requirement(db, requirement_id=req.id, buyer=buyer)
    audit(
        db,
        actor_id=admin.id,
        action="seed.demo_scenario_created",
        entity_type="DemoScenario",
        new_value={"scenario": "2,000 kg tomato pooled marketplace flow"},
    )
    db.commit()


def _data_source(
    name: str,
    official_source: str,
    url: str,
    access_method: str,
    format: str,
    fields: list[str],
    geographic_coverage: str,
    time_range: str,
    update_frequency: str,
    license: str,
    usable_for_ml: bool,
    limitations: str,
):
    from backend.app.models import DataSource

    return DataSource(
        name=name,
        official_source=official_source,
        url=url,
        access_method=access_method,
        format=format,
        fields=fields,
        geographic_coverage=geographic_coverage,
        time_range=time_range,
        update_frequency=update_frequency,
        license=license,
        usable_for_ml=usable_for_ml,
        limitations=limitations,
    )

