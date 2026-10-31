"""Generate 1,020 realistic retail mock records across 10 stores in 5 states
and ingest them directly into RetailIQ database.
"""

import os
import sys
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Project directories
project_root = os.path.abspath("RetailIQ")
backend_dir = os.path.join(project_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

import asyncio
from sqlalchemy import select, text, update
from app.core.database import async_session_factory
from app.models import Organization, User, Product, Store, Sale, InventoryLevel
from app.services.data_service import TenantDataService

stores_data = [
    {"code": "CA_1", "name": "CA_1 - Los Angeles Downtown", "city": "Los Angeles", "region": "CA", "mult": 1.25},
    {"code": "CA_2", "name": "CA_2 - San Francisco Market", "city": "San Francisco", "region": "CA", "mult": 1.10},
    {"code": "CA_3", "name": "CA_3 - San Diego Mission", "city": "San Diego", "region": "CA", "mult": 0.95},
    {"code": "TX_1", "name": "TX_1 - Dallas Northpark", "city": "Dallas", "region": "TX", "mult": 1.15},
    {"code": "TX_2", "name": "TX_2 - Austin Domain", "city": "Austin", "region": "TX", "mult": 1.05},
    {"code": "TX_3", "name": "TX_3 - Houston Galleria", "city": "Houston", "region": "TX", "mult": 1.20},
    {"code": "WI_1", "name": "WI_1 - Milwaukee Bayshore", "city": "Milwaukee", "region": "WI", "mult": 0.85},
    {"code": "WI_2", "name": "WI_2 - Madison Capitol", "city": "Madison", "region": "WI", "mult": 0.80},
    {"code": "NY_1", "name": "NY_1 - New York Herald Sq", "city": "New York", "region": "NY", "mult": 1.40},
    {"code": "FL_1", "name": "FL_1 - Miami Brickell", "city": "Miami", "region": "FL", "mult": 1.05},
]

products_data = [
    {"sku": "FOODS_3_001", "name": "Premium Arabica Coffee 12oz", "category": "FOODS", "price": 14.99, "cost": 8.50, "base_demand": 22.0},
    {"sku": "FOODS_3_002", "name": "Organic Creamy Peanut Butter", "category": "FOODS", "price": 5.49, "cost": 3.10, "base_demand": 14.0},
    {"sku": "HOBBIES_1_001", "name": "Ergonomic Wireless Mouse", "category": "HOBBIES", "price": 29.99, "cost": 16.00, "base_demand": 7.0},
    {"sku": "HOBBIES_1_002", "name": "Noise Isolating Earbuds", "category": "HOBBIES", "price": 39.99, "cost": 22.00, "base_demand": 5.0},
    {"sku": "HOUSEHOLD_1_001", "name": "Microfiber Cleaning Cloths 10pk", "category": "HOUSEHOLD", "price": 8.50, "cost": 4.25, "base_demand": 16.0},
    {"sku": "HOUSEHOLD_2_005", "name": "Stainless Steel Food Container Set", "category": "HOUSEHOLD", "price": 24.99, "cost": 13.50, "base_demand": 6.5},
]

# Strategic inventory stock overrides to enable rich Multi-Agent Decision triggers
custom_stocks = {
    # Store CA_1 is facing stockout on coffee, while sister store CA_2 has large surplus (triggers Inter-Store Transfer!)
    ("CA_1", "FOODS_3_001"): 14,
    ("CA_2", "FOODS_3_001"): 230,
    # Store TX_1 is low on wireless mouse, while TX_3 has surplus (triggers Inter-Store Transfer!)
    ("TX_1", "HOBBIES_1_001"): 6,
    ("TX_3", "HOBBIES_1_001"): 140,
    # NY_1 is running critically low on peanut butter with no local sister store having surplus (triggers Supplier Replenishment PO!)
    ("NY_1", "FOODS_3_002"): 12,
    # WI_1 is severely overstocked on Stainless Containers (triggers Markdown / Promo liquidation!)
    ("WI_1", "HOUSEHOLD_2_005"): 340,
    ("WI_2", "HOUSEHOLD_2_005"): 290,
    # FL_1 has fast growing demand for earbuds (triggers DC Allocation Increase!)
    ("FL_1", "HOBBIES_1_002"): 15,
}

def generate_records():
    random.seed(42)
    np.random.seed(42)

    start_date = datetime(2026, 10, 8)
    rows = []

    for day_offset in range(17):
        current_date = start_date + timedelta(days=day_offset)
        date_str = current_date.strftime("%Y-%m-%d")
        day_of_week = current_date.weekday()
        # Weekend boost (Friday=4, Saturday=5, Sunday=6)
        weekend_mult = 1.35 if day_of_week in [4, 5, 6] else 1.0

        for s in stores_data:
            store_id = s["code"]
            store_mult = s["mult"]

            for p in products_data:
                item_id = p["sku"]
                base_demand = p["base_demand"]
                price = p["price"]
                category = p["category"]

                # Expected daily sales with store traffic, day-of-week, and gaussian randomness
                expected = base_demand * store_mult * weekend_mult
                noise = np.random.normal(0, max(1.2, expected * 0.15))
                sales = int(max(0, round(expected + noise)))

                # Determine on-hand stock for this pair
                if (store_id, item_id) in custom_stocks:
                    stock = custom_stocks[(store_id, item_id)]
                else:
                    # Balanced stock: 15-25 days of average velocity
                    stock = int(round(expected * random.uniform(15, 24)))

                rows.append({
                    "date": date_str,
                    "item_id": item_id,
                    "store_id": store_id,
                    "sales": sales,
                    "sell_price": price,
                    "category": category,
                    "current_stock": stock,
                })

    return pd.DataFrame(rows)

async def main():
    print("Generating mock sales data...")
    df = generate_records()
    print(f"Generated {len(df)} records across {df['store_id'].nunique()} stores and {df['item_id'].nunique()} products.")

    # Save to CSV
    csv_path = os.path.join(project_root, "mock_1000_sales.csv")
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV to {csv_path}")

    # Save to Excel (.xlsx)
    xlsx_path = os.path.join(project_root, "mock_1000_sales.xlsx")
    df.to_excel(xlsx_path, index=False, engine="openpyxl")
    print(f"Saved Excel to {xlsx_path}")

    # Ingest directly into active organization
    async with async_session_factory() as db:
        res_org = await db.execute(select(Organization))
        org = res_org.scalars().first()
        if not org:
            print("Error: No organization found in database.")
            return

        res_user = await db.execute(select(User))
        user = res_user.scalars().first()
        user_id = user.id if user else None

        print(f"Purging old data for Org '{org.name}' ({org.id})...")
        await db.execute(text("DELETE FROM sales WHERE organization_id = :org_id"), {"org_id": org.id})
        await db.execute(text("DELETE FROM inventory_levels WHERE organization_id = :org_id"), {"org_id": org.id})
        await db.execute(text("DELETE FROM forecasts WHERE header_id IN (SELECT id FROM forecast_headers WHERE organization_id = :org_id)"), {"org_id": org.id})
        await db.execute(text("DELETE FROM forecast_headers WHERE organization_id = :org_id"), {"org_id": org.id})
        await db.execute(text("DELETE FROM datasets WHERE organization_id = :org_id"), {"org_id": org.id})
        await db.execute(text("DELETE FROM import_jobs WHERE organization_id = :org_id"), {"org_id": org.id})
        await db.execute(text("DELETE FROM products WHERE organization_id = :org_id"), {"org_id": org.id})
        await db.execute(text("DELETE FROM stores WHERE organization_id = :org_id"), {"org_id": org.id})
        await db.commit()

        print("Ingesting new 1,020 records into database tables...")
        res = await TenantDataService.ingest_dataframe(
            db=db,
            organization_id=org.id,
            df=df,
            source="mock_1000_sales.xlsx",
            created_by=user_id,
        )
        print(f"Ingestion result: {res}")

        # Enrich Store metadata (cities, regions, full names)
        print("Enriching Store metadata (cities, regions)...")
        for s in stores_data:
            await db.execute(
                update(Store)
                .where(Store.organization_id == org.id, Store.store_code == s["code"])
                .values(name=s["name"], city=s["city"], region=s["region"])
            )

        # Enrich Product metadata (human names, unit costs)
        print("Enriching Product metadata (names, unit costs)...")
        for p in products_data:
            await db.execute(
                update(Product)
                .where(Product.organization_id == org.id, Product.sku == p["sku"])
                .values(name=p["name"], unit_cost=p["cost"])
            )

        await db.commit()
        print("All data successfully committed to SQLite database!")

if __name__ == "__main__":
    asyncio.run(main())
