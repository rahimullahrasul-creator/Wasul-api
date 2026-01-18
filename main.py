"""
Oman Address API - MVP
A system to register and lookup home addresses in Oman where traditional addressing doesn't exist
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import sqlite3
import hashlib
import random
import string

app = FastAPI(
    title="Wasul API",
    description="Deliver to any home in Oman - Address registration and lookup system",
    version="1.0.0"
)

# CORS middleware for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def init_db():
    conn = sqlite3.connect('oman_addresses.db')
    c = conn.cursor()
    
    # Addresses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address_code TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            po_box TEXT,
            area TEXT,
            city TEXT,
            delivery_notes TEXT,
            created_at TEXT NOT NULL,
            verified BOOLEAN DEFAULT 0,
            successful_deliveries INTEGER DEFAULT 0
        )
    ''')
    
    # Deliveries table (for tracking and improving data)
    c.execute('''
        CREATE TABLE IF NOT EXISTS deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address_code TEXT NOT NULL,
            delivery_partner TEXT,
            success BOOLEAN,
            feedback TEXT,
            delivered_at TEXT NOT NULL,
            FOREIGN KEY (address_code) REFERENCES addresses(address_code)
        )
    ''')
    
    # API keys table (for delivery partners)
    c.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_name TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            lookups_used INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            active BOOLEAN DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Pydantic models
class AddressRegistration(BaseModel):
    phone: str = Field(..., description="Phone number with country code (e.g., 96891234567)")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    po_box: Optional[str] = Field(None, description="P.O. Box number if available")
    area: Optional[str] = Field(None, description="Area/neighborhood name")
    city: str = Field(default="Muscat", description="City name")
    delivery_notes: Optional[str] = Field(None, description="Special delivery instructions")

class AddressLookup(BaseModel):
    address_code: str
    phone: str
    latitude: float
    longitude: float
    po_box: Optional[str]
    area: Optional[str]
    city: str
    delivery_notes: Optional[str]
    google_maps_link: str
    verified: bool
    successful_deliveries: int

class DeliveryVerification(BaseModel):
    address_code: str = Field(..., description="The address code used for delivery")
    success: bool = Field(..., description="Whether delivery was successful")
    feedback: Optional[str] = Field(None, description="Any feedback or issues")

class APIKeyRequest(BaseModel):
    partner_name: str = Field(..., description="Name of delivery partner/restaurant")

# Helper functions
def generate_address_code(city: str) -> str:
    """Generate unique address code like OM-MUS-4729A"""
    city_codes = {
        "Muscat": "MUS",
        "Salalah": "SAL",
        "Sohar": "SOH",
        "Nizwa": "NIZ",
    }
    city_code = city_codes.get(city, "OTH")
    random_part = ''.join(random.choices(string.digits, k=4))
    letter = random.choice(string.ascii_uppercase)
    return f"OM-{city_code}-{random_part}{letter}"

def generate_api_key() -> str:
    """Generate API key for delivery partners"""
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    return f"omaddr_{hashlib.sha256(random_string.encode()).hexdigest()[:32]}"

def verify_api_key(api_key: str) -> bool:
    """Verify if API key is valid and active"""
    conn = sqlite3.connect('oman_addresses.db')
    c = conn.cursor()
    c.execute('SELECT active FROM api_keys WHERE api_key = ?', (api_key,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

def increment_lookup_count(api_key: str):
    """Increment lookup counter for billing purposes"""
    conn = sqlite3.connect('oman_addresses.db')
    c = conn.cursor()
    c.execute('UPDATE api_keys SET lookups_used = lookups_used + 1 WHERE api_key = ?', (api_key,))
    conn.commit()
    conn.close()

# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Landing page with API documentation"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Oman Address API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
            h1 { color: #c8102e; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { display: inline-block; padding: 5px 10px; border-radius: 3px; font-weight: bold; color: white; }
            .post { background: #49cc90; }
            .get { background: #61affe; }
            code { background: #e8e8e8; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🏠 Wasul API</h1>
        <p>Solving the addressing problem in Oman - one delivery at a time.</p>
        
        <h2>Quick Links</h2>
        <ul>
            <li><a href="/docs">Interactive API Documentation</a></li>
            <li><a href="/admin">Admin Dashboard</a></li>
            <li><a href="/stats">System Statistics</a></li>
        </ul>
        
        <h2>Core Endpoints</h2>
        
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/register-address</code>
            <p>Register a new home address. Residents use this to add their location.</p>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span> <code>/api/lookup</code>
            <p>Lookup address by phone number or address code. Delivery partners use this.</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/verify-delivery</code>
            <p>Mark delivery as successful/failed. Improves data quality.</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span> <code>/api/request-key</code>
            <p>Request API key for delivery partners.</p>
        </div>
        
        <h2>Example Integration</h2>
        <pre>
# Python example for delivery partners
import requests

API_KEY = "your_api_key_here"
headers = {"X-API-Key": API_KEY}

# Lookup address
response = requests.get(
    "http://your-api-url/api/lookup",
    params={"phone": "96891234567"},
    headers=headers
)

address = response.json()
print(f"Navigate to: {address['google_maps_link']}")
        </pre>
    </body>
    </html>
    """

@app.post("/api/register-address", response_model=dict)
async def register_address(address: AddressRegistration):
    """
    Register a new home address
    
    Residents use this to add their home location to the system.
    Returns a unique address code they can use for deliveries.
    """
    try:
        conn = sqlite3.connect('oman_addresses.db')
        c = conn.cursor()
        
        # Check if phone already registered
        c.execute('SELECT address_code FROM addresses WHERE phone = ?', (address.phone,))
        existing = c.fetchone()
        
        if existing:
            conn.close()
            raise HTTPException(
                status_code=400, 
                detail=f"Phone number already registered with code: {existing[0]}"
            )
        
        # Generate unique address code
        address_code = generate_address_code(address.city)
        
        # Insert new address
        c.execute('''
            INSERT INTO addresses 
            (address_code, phone, latitude, longitude, po_box, area, city, delivery_notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            address_code,
            address.phone,
            address.latitude,
            address.longitude,
            address.po_box,
            address.area,
            address.city,
            address.delivery_notes,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "address_code": address_code,
            "message": "Address registered successfully! Use this code when ordering.",
            "google_maps_link": f"https://www.google.com/maps?q={address.latitude},{address.longitude}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lookup", response_model=AddressLookup)
async def lookup_address(
    phone: Optional[str] = Query(None, description="Phone number to lookup"),
    address_code: Optional[str] = Query(None, description="Address code to lookup"),
    api_key: str = Query(..., alias="X-API-Key", description="Your API key")
):
    """
    Lookup address by phone number or address code
    
    Delivery partners use this to find where to deliver.
    Requires valid API key.
    """
    
    # Verify API key
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    if not phone and not address_code:
        raise HTTPException(status_code=400, detail="Must provide either phone or address_code")
    
    try:
        conn = sqlite3.connect('oman_addresses.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        if phone:
            c.execute('SELECT * FROM addresses WHERE phone = ?', (phone,))
        else:
            c.execute('SELECT * FROM addresses WHERE address_code = ?', (address_code,))
        
        result = c.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Address not found")
        
        # Increment lookup counter for billing
        increment_lookup_count(api_key)
        
        return AddressLookup(
            address_code=result['address_code'],
            phone=result['phone'],
            latitude=result['latitude'],
            longitude=result['longitude'],
            po_box=result['po_box'],
            area=result['area'],
            city=result['city'],
            delivery_notes=result['delivery_notes'],
            google_maps_link=f"https://www.google.com/maps?q={result['latitude']},{result['longitude']}",
            verified=bool(result['verified']),
            successful_deliveries=result['successful_deliveries']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/verify-delivery")
async def verify_delivery(
    verification: DeliveryVerification,
    api_key: str = Query(..., alias="X-API-Key", description="Your API key")
):
    """
    Mark delivery as successful or failed
    
    Helps improve data quality and verify addresses.
    Successful deliveries increase address reliability score.
    """
    
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    try:
        conn = sqlite3.connect('oman_addresses.db')
        c = conn.cursor()
        
        # Get partner name
        c.execute('SELECT partner_name FROM api_keys WHERE api_key = ?', (api_key,))
        partner = c.fetchone()
        partner_name = partner[0] if partner else "Unknown"
        
        # Record delivery
        c.execute('''
            INSERT INTO deliveries (address_code, delivery_partner, success, feedback, delivered_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            verification.address_code,
            partner_name,
            verification.success,
            verification.feedback,
            datetime.now().isoformat()
        ))
        
        # Update address success counter and verification status
        if verification.success:
            c.execute('''
                UPDATE addresses 
                SET successful_deliveries = successful_deliveries + 1,
                    verified = CASE WHEN successful_deliveries >= 2 THEN 1 ELSE verified END
                WHERE address_code = ?
            ''', (verification.address_code,))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Delivery verification recorded"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/request-key")
async def request_api_key(request: APIKeyRequest):
    """
    Request an API key for delivery partners
    
    In production, this would require approval/payment.
    For MVP, it auto-generates a key for testing.
    """
    try:
        conn = sqlite3.connect('oman_addresses.db')
        c = conn.cursor()
        
        api_key = generate_api_key()
        
        c.execute('''
            INSERT INTO api_keys (partner_name, api_key, created_at)
            VALUES (?, ?, ?)
        ''', (request.partner_name, api_key, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "partner_name": request.partner_name,
            "api_key": api_key,
            "message": "API key generated. Keep this secure!"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        conn = sqlite3.connect('oman_addresses.db')
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM addresses')
        total_addresses = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM addresses WHERE verified = 1')
        verified_addresses = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM deliveries WHERE success = 1')
        successful_deliveries = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM api_keys WHERE active = 1')
        active_partners = c.fetchone()[0]
        
        c.execute('SELECT SUM(lookups_used) FROM api_keys')
        total_lookups = c.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_addresses": total_addresses,
            "verified_addresses": verified_addresses,
            "successful_deliveries": successful_deliveries,
            "active_partners": active_partners,
            "total_lookups": total_lookups,
            "revenue_estimate_usd": total_lookups * 0.15  # $0.15 per lookup
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    """Simple admin dashboard to view all addresses"""
    try:
        conn = sqlite3.connect('oman_addresses.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('SELECT * FROM addresses ORDER BY created_at DESC')
        addresses = c.fetchall()
        
        c.execute('SELECT * FROM api_keys WHERE active = 1')
        partners = c.fetchall()
        
        conn.close()
        
        addresses_html = ""
        for addr in addresses:
            verified_badge = "✓ Verified" if addr['verified'] else "⏳ Pending"
            addresses_html += f"""
            <tr>
                <td>{addr['address_code']}</td>
                <td>{addr['phone']}</td>
                <td>{addr['city']} - {addr['area'] or 'N/A'}</td>
                <td><a href="https://www.google.com/maps?q={addr['latitude']},{addr['longitude']}" target="_blank">View Map</a></td>
                <td>{addr['delivery_notes'] or 'None'}</td>
                <td>{verified_badge}</td>
                <td>{addr['successful_deliveries']}</td>
            </tr>
            """
        
        partners_html = ""
        for partner in partners:
            partners_html += f"""
            <tr>
                <td>{partner['partner_name']}</td>
                <td><code>{partner['api_key']}</code></td>
                <td>{partner['lookups_used']}</td>
                <td>${partner['lookups_used'] * 0.15:.2f}</td>
            </tr>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Dashboard - Oman Address API</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #c8102e; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #c8102e; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                code {{ background: #e8e8e8; padding: 2px 5px; border-radius: 3px; }}
                .section {{ margin: 40px 0; }}
            </style>
        </head>
        <body>
            <h1>📊 Admin Dashboard</h1>
            <p><a href="/">← Back to Home</a> | <a href="/docs">API Docs</a> | <a href="/stats">Statistics</a></p>
            
            <div class="section">
                <h2>Registered Addresses ({len(addresses)})</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Address Code</th>
                            <th>Phone</th>
                            <th>Location</th>
                            <th>Map</th>
                            <th>Delivery Notes</th>
                            <th>Status</th>
                            <th>Deliveries</th>
                        </tr>
                    </thead>
                    <tbody>
                        {addresses_html if addresses_html else '<tr><td colspan="7">No addresses registered yet</td></tr>'}
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>Delivery Partners ({len(partners)})</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Partner Name</th>
                            <th>API Key</th>
                            <th>Lookups Used</th>
                            <th>Revenue Generated</th>
                        </tr>
                    </thead>
                    <tbody>
                        {partners_html if partners_html else '<tr><td colspan="4">No partners registered yet</td></tr>'}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        
    except Exception as e:
        return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
