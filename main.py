"""
Wasul API — Address registration and lookup for Oman
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
import sqlite3
import hashlib
import random
import string
import os

app = FastAPI(
    title="Wasul API",
    description="Address registration and lookup system for home delivery in Oman",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# CONFIGURATION — Edit these values to customize invoices
# ============================================================
INVOICE_CONFIG = {
    "from_name": "Wasul",
    "from_address": "Rahim Rasul\nrahimullahrasul@gmail.com\nPlano, TX",
    "payment_instructions": (
        "Bank Transfer: [Your Bank] — Routing: XXXXXXXX — Account: XXXXXXXX\n"
        "Wise: rahimullahrasul@gmail.com\n"
        "Payment terms: Net 15 days from invoice date"
    ),
    "default_rate_per_lookup": 0.15,
    "payment_terms_days": 15,
}

# ============================================================
# DATABASE
# ============================================================
def init_db():
    conn = sqlite3.connect('oman_addresses.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS addresses (
        id INTEGER PRIMARY KEY AUTOINCREMENT, address_code TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL,
        po_box TEXT, area TEXT, city TEXT, delivery_notes TEXT,
        created_at TEXT NOT NULL, verified BOOLEAN DEFAULT 0, successful_deliveries INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT, address_code TEXT NOT NULL,
        delivery_partner TEXT, success BOOLEAN, feedback TEXT, delivered_at TEXT NOT NULL,
        FOREIGN KEY (address_code) REFERENCES addresses(address_code))''')
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT, partner_name TEXT NOT NULL,
        api_key TEXT UNIQUE NOT NULL, lookups_used INTEGER DEFAULT 0,
        created_at TEXT NOT NULL, active BOOLEAN DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_number TEXT UNIQUE NOT NULL,
        partner_name TEXT NOT NULL, api_key TEXT NOT NULL, billing_period TEXT NOT NULL,
        lookups INT NOT NULL, deliveries_verified INT NOT NULL, rate_per_lookup REAL NOT NULL,
        subtotal REAL NOT NULL, tax REAL DEFAULT 0, total REAL NOT NULL,
        created_at TEXT NOT NULL, status TEXT DEFAULT 'unpaid')''')
    conn.commit()
    conn.close()

init_db()

# ============================================================
# MODELS
# ============================================================
class AddressRegistration(BaseModel):
    phone: str = Field(..., description="Phone number with country code")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    po_box: Optional[str] = None
    area: Optional[str] = None
    city: str = Field(default="Muscat")
    delivery_notes: Optional[str] = None

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
    address_code: str
    success: bool
    feedback: Optional[str] = None

class APIKeyRequest(BaseModel):
    partner_name: str

# ============================================================
# HELPERS
# ============================================================
def generate_address_code(city: str) -> str:
    city_codes = {"Muscat": "MUS", "Salalah": "SAL", "Sohar": "SOH", "Nizwa": "NIZ"}
    city_code = city_codes.get(city, "OTH")
    return f"OM-{city_code}-{''.join(random.choices(string.digits, k=4))}{random.choice(string.ascii_uppercase)}"

def generate_api_key() -> str:
    r = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    return f"omaddr_{hashlib.sha256(r.encode()).hexdigest()[:32]}"

def verify_api_key(api_key: str) -> bool:
    conn = sqlite3.connect('oman_addresses.db')
    c = conn.cursor()
    c.execute('SELECT active FROM api_keys WHERE api_key = ?', (api_key,))
    result = c.fetchone()
    conn.close()
    return result and result[0] == 1

def increment_lookup_count(api_key: str):
    conn = sqlite3.connect('oman_addresses.db')
    c = conn.cursor()
    c.execute('UPDATE api_keys SET lookups_used = lookups_used + 1 WHERE api_key = ?', (api_key,))
    conn.commit()
    conn.close()

def get_next_invoice_number():
    conn = sqlite3.connect('oman_addresses.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM invoices')
    count = c.fetchone()[0]
    conn.close()
    return f"WAS-{datetime.now().year}-{count + 1:04d}"
PAGE_CSS = """<style>
:root{--o5:#e8682a;--o6:#d45a1f;--o0:#fef5f0;--s1:#f9f6f2;--s2:#f0ebe3;--ch:#1a1a1a;--sl:#4a4a4a;--mu:#7a7a7a;--wh:#fff;--g5:#16a34a;--g0:#f0fdf4}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:var(--ch);background:var(--s1);-webkit-font-smoothing:antialiased}
.top-bar{background:var(--wh);padding:20px 40px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--s2)}
.top-bar-logo{font-size:1.4rem;font-weight:700;color:var(--o5);text-decoration:none;letter-spacing:-.5px}
.top-bar-nav{display:flex;gap:24px}
.top-bar-nav a{text-decoration:none;color:var(--sl);font-size:.85rem;font-weight:500;padding:6px 12px;border-radius:6px;transition:all .15s}
.top-bar-nav a:hover{background:var(--s2);color:var(--ch)}
.top-bar-nav a.active{background:var(--o0);color:var(--o5)}
.container{max-width:1000px;margin:0 auto;padding:40px}
h1{font-size:1.8rem;font-weight:700;margin-bottom:8px;letter-spacing:-.5px}
h1 span{color:var(--o5)}
.subtitle{color:var(--mu);font-size:.95rem;margin-bottom:40px}
.card{background:var(--wh);border-radius:12px;padding:32px;margin-bottom:24px;box-shadow:0 1px 3px rgba(0,0,0,.03)}
.card h2{font-size:1.1rem;font-weight:700;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid var(--s2)}
.endpoint{display:flex;align-items:flex-start;gap:12px;padding:16px 0;border-bottom:1px solid var(--s1)}
.endpoint:last-child{border-bottom:none}
.method-badge{display:inline-block;padding:4px 10px;border-radius:5px;font-size:.72rem;font-weight:700;letter-spacing:.5px;flex-shrink:0;width:48px;text-align:center}
.method-badge.post{background:#dcfce7;color:#166534}
.method-badge.get{background:#dbeafe;color:#1e40af}
.endpoint-info{flex:1}
.endpoint-path{font-family:'SF Mono','Fira Code',monospace;font-size:.88rem;font-weight:600;color:var(--ch);margin-bottom:2px}
.endpoint-desc{font-size:.82rem;color:var(--mu)}
.code-block{background:var(--ch);border-radius:10px;overflow:hidden}
.code-header{padding:12px 20px;display:flex;align-items:center;gap:6px;border-bottom:1px solid rgba(255,255,255,.06)}
.code-dot{width:8px;height:8px;border-radius:50%}
.code-dot.r{background:#ff5f57}.code-dot.y{background:#febc2e}.code-dot.g{background:#28c840}
.code-body{padding:20px;font-family:'SF Mono','Fira Code',monospace;font-size:.78rem;line-height:1.8;color:#a0a0a0;overflow-x:auto}
.code-body .kw{color:#c792ea}.code-body .str{color:#c3e88d}.code-body .url{color:#82aaff}.code-body .cm{color:#546e7a}.code-body .key{color:#f78c6c}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:32px}
.stat-card{background:var(--wh);border-radius:12px;padding:24px;text-align:center}
.stat-value{font-size:2rem;font-weight:700;color:var(--ch)}
.stat-value.orange{color:var(--o5)}.stat-value.green{color:var(--g5)}
.stat-label{font-size:.75rem;text-transform:uppercase;letter-spacing:1px;color:var(--mu);margin-top:4px;font-weight:600}
table{width:100%;border-collapse:collapse}
th{text-align:left;font-size:.72rem;text-transform:uppercase;letter-spacing:1px;color:var(--mu);font-weight:600;padding:12px 16px;border-bottom:1px solid var(--s2)}
td{padding:14px 16px;font-size:.88rem;border-bottom:1px solid var(--s1);color:var(--sl)}
tr:last-child td{border-bottom:none}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:.72rem;font-weight:600}
.badge.verified{background:var(--g0);color:var(--g5)}
.badge.pending{background:var(--s2);color:var(--mu)}
.badge.unpaid{background:#fef2f2;color:#dc2626}
.badge.paid{background:var(--g0);color:var(--g5)}
.map-link{color:var(--o5);text-decoration:none;font-weight:500;font-size:.82rem}
.map-link:hover{text-decoration:underline}
code{background:var(--s1);padding:2px 6px;border-radius:4px;font-size:.8rem;font-family:'SF Mono','Fira Code',monospace}
.empty-state{text-align:center;padding:40px;color:var(--mu)}
.btn{display:inline-block;padding:8px 16px;border-radius:6px;font-size:.82rem;font-weight:600;text-decoration:none;cursor:pointer;border:none;transition:all .15s}
.btn-orange{background:var(--o5);color:var(--wh)}.btn-orange:hover{background:var(--o6)}
.btn-sm{padding:5px 12px;font-size:.75rem}
.btn-outline{background:transparent;color:var(--sl);border:1.5px solid var(--s2)}
.btn-outline:hover{border-color:var(--o5);color:var(--o5)}
@media(max-width:768px){.container{padding:20px}.top-bar{padding:16px 20px}.card{padding:20px}.stats-grid{grid-template-columns:repeat(2,1fr)}}
</style>"""

# ============================================================
# ROUTES — OVERVIEW PAGE
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Wasul API</title>{PAGE_CSS}</head><body>
    <div class="top-bar"><a href="/" class="top-bar-logo">Wasul API</a><div class="top-bar-nav"><a href="/" class="active">Overview</a><a href="/docs">Documentation</a><a href="/admin">Dashboard</a><a href="/admin/invoices">Invoices</a></div></div>
    <div class="container">
        <h1>Wasul <span>API</span></h1>
        <p class="subtitle">Address registration and lookup for home delivery in Oman</p>
        <div class="card"><h2>Endpoints</h2>
            <div class="endpoint"><span class="method-badge post">POST</span><div class="endpoint-info"><div class="endpoint-path">/api/register-address</div><div class="endpoint-desc">Register a new home address. Returns a unique Wasul code.</div></div></div>
            <div class="endpoint"><span class="method-badge get">GET</span><div class="endpoint-info"><div class="endpoint-path">/api/lookup</div><div class="endpoint-desc">Look up address by phone number or Wasul code. Requires API key.</div></div></div>
            <div class="endpoint"><span class="method-badge post">POST</span><div class="endpoint-info"><div class="endpoint-path">/api/verify-delivery</div><div class="endpoint-desc">Mark delivery as successful or failed. Requires API key.</div></div></div>
            <div class="endpoint"><span class="method-badge post">POST</span><div class="endpoint-info"><div class="endpoint-path">/api/request-key</div><div class="endpoint-desc">Request an API key for delivery partners.</div></div></div>
        </div>
        <div class="card"><h2>Quick Start</h2>
            <div class="code-block"><div class="code-header"><div class="code-dot r"></div><div class="code-dot y"></div><div class="code-dot g"></div></div>
            <div class="code-body"><span class="cm"># 1. Get an API key</span><br><span class="kw">POST</span> <span class="url">/api/request-key</span><br>{{ <span class="key">"partner_name"</span>: <span class="str">"Your Restaurant"</span> }}<br><br><span class="cm"># 2. Look up a customer address</span><br><span class="kw">GET</span> <span class="url">/api/lookup?phone=96891234567&X-API-Key=your_key</span><br><br><span class="cm"># Response</span><br>{{<br>&nbsp;&nbsp;<span class="key">"address_code"</span>: <span class="str">"OM-MUS-4729A"</span>,<br>&nbsp;&nbsp;<span class="key">"area"</span>: <span class="str">"Al Khuwair"</span>,<br>&nbsp;&nbsp;<span class="key">"city"</span>: <span class="str">"Muscat"</span>,<br>&nbsp;&nbsp;<span class="key">"google_maps_link"</span>: <span class="str">"maps.google.com/..."</span>,<br>&nbsp;&nbsp;<span class="key">"verified"</span>: <span class="kw">true</span><br>}}</div></div>
        </div>
        <p style="text-align:center;color:var(--mu);font-size:.85rem;margin-top:40px"><a href="/docs" style="color:var(--o5);text-decoration:none;font-weight:600">Full interactive documentation</a></p>
    </div></body></html>"""

# ============================================================
# ROUTES — API ENDPOINTS
# ============================================================

@app.post("/api/register-address", response_model=dict)
async def register_address(address: AddressRegistration):
    try:
        conn = sqlite3.connect('oman_addresses.db')
        c = conn.cursor()
        c.execute('SELECT address_code FROM addresses WHERE phone = ?', (address.phone,))
        existing = c.fetchone()
        if existing:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Phone already registered: {existing[0]}")
        address_code = generate_address_code(address.city)
        c.execute('INSERT INTO addresses (address_code,phone,latitude,longitude,po_box,area,city,delivery_notes,created_at) VALUES (?,?,?,?,?,?,?,?,?)',
            (address_code, address.phone, address.latitude, address.longitude, address.po_box, address.area, address.city, address.delivery_notes, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return {"success": True, "address_code": address_code, "message": "Address registered successfully!",
                "google_maps_link": f"https://www.google.com/maps?q={address.latitude},{address.longitude}"}
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/lookup", response_model=AddressLookup)
async def lookup_address(phone: Optional[str] = Query(None), address_code: Optional[str] = Query(None), api_key: str = Query(..., alias="X-API-Key")):
    if not verify_api_key(api_key): raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    if not phone and not address_code: raise HTTPException(status_code=400, detail="Must provide phone or address_code")
    try:
        conn = sqlite3.connect('oman_addresses.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        if phone: c.execute('SELECT * FROM addresses WHERE phone = ?', (phone,))
        else: c.execute('SELECT * FROM addresses WHERE address_code = ?', (address_code,))
        result = c.fetchone()
        conn.close()
        if not result: raise HTTPException(status_code=404, detail="Address not found")
        increment_lookup_count(api_key)
        return AddressLookup(address_code=result['address_code'], phone=result['phone'],
            latitude=result['latitude'], longitude=result['longitude'], po_box=result['po_box'],
            area=result['area'], city=result['city'], delivery_notes=result['delivery_notes'],
            google_maps_link=f"https://www.google.com/maps?q={result['latitude']},{result['longitude']}",
            verified=bool(result['verified']), successful_deliveries=result['successful_deliveries'])
    except HTTPException: raise
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/verify-delivery")
async def verify_delivery(verification: DeliveryVerification, api_key: str = Query(..., alias="X-API-Key")):
    if not verify_api_key(api_key): raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    try:
        conn = sqlite3.connect('oman_addresses.db')
        c = conn.cursor()
        c.execute('SELECT partner_name FROM api_keys WHERE api_key = ?', (api_key,))
        partner = c.fetchone()
        partner_name = partner[0] if partner else "Unknown"
        c.execute('INSERT INTO deliveries (address_code,delivery_partner,success,feedback,delivered_at) VALUES (?,?,?,?,?)',
            (verification.address_code, partner_name, verification.success, verification.feedback, datetime.now().isoformat()))
        if verification.success:
            c.execute('UPDATE addresses SET successful_deliveries=successful_deliveries+1, verified=CASE WHEN successful_deliveries>=2 THEN 1 ELSE verified END WHERE address_code=?',
                (verification.address_code,))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Delivery verification recorded"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/request-key")
async def request_api_key(request: APIKeyRequest):
    try:
        conn = sqlite3.connect('oman_addresses.db')
        c = conn.cursor()
        api_key = generate_api_key()
        c.execute('INSERT INTO api_keys (partner_name,api_key,created_at) VALUES (?,?,?)',
            (request.partner_name, api_key, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return {"success": True, "partner_name": request.partner_name, "api_key": api_key, "message": "API key generated. Keep this secure!"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    try:
        conn = sqlite3.connect('oman_addresses.db')
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM addresses'); ta = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM addresses WHERE verified=1'); va = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM deliveries WHERE success=1'); sd = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM api_keys WHERE active=1'); ap = c.fetchone()[0]
        c.execute('SELECT SUM(lookups_used) FROM api_keys'); tl = c.fetchone()[0] or 0
        conn.close()
        return {"total_addresses": ta, "verified_addresses": va, "successful_deliveries": sd,
                "active_partners": ap, "total_lookups": tl, "revenue_estimate_usd": tl * INVOICE_CONFIG['default_rate_per_lookup']}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# ROUTES — INVOICING
# ============================================================

@app.get("/api/generate-invoice/{partner_id}")
async def generate_invoice(partner_id: int):
    try:
        from invoice_generator import generate_invoice_pdf
        conn = sqlite3.connect('oman_addresses.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM api_keys WHERE id=? AND active=1', (partner_id,))
        partner = c.fetchone()
        if not partner:
            conn.close()
            raise HTTPException(status_code=404, detail="Partner not found")
        c.execute('SELECT COUNT(*) FROM deliveries WHERE delivery_partner=? AND success=1', (partner['partner_name'],))
        dv = c.fetchone()[0]
        conn.close()

        now = datetime.now()
        inv_num = get_next_invoice_number()
        rate = INVOICE_CONFIG['default_rate_per_lookup']
        lookups = partner['lookups_used']
        subtotal = round(lookups * rate, 2)
        due = now + timedelta(days=INVOICE_CONFIG['payment_terms_days'])
        pm, py = (12, now.year - 1) if now.month == 1 else (now.month - 1, now.year)
        billing_period = datetime(py, pm, 1).strftime('%B %Y')

        data = {
            'invoice_number': inv_num, 'from_name': INVOICE_CONFIG['from_name'],
            'from_address': INVOICE_CONFIG['from_address'], 'partner_name': partner['partner_name'],
            'partner_address': '', 'invoice_date': now.strftime('%B %d, %Y'),
            'due_date': due.strftime('%B %d, %Y'), 'billing_period': billing_period,
            'line_items': [
                {'description': 'API Address Lookups', 'quantity': str(lookups), 'rate': f'${rate:.2f}', 'amount': f'${subtotal:.2f}'},
                {'description': 'Delivery Verifications', 'quantity': str(dv), 'rate': 'Included', 'amount': '$0.00'},
            ],
            'subtotal': f'${subtotal:.2f}', 'tax': '$0.00', 'total': f'${subtotal:.2f}',
            'total_lookups': lookups, 'deliveries_verified': dv,
            'api_key_preview': f'{partner["api_key"][:16]}...{partner["api_key"][-6:]}',
            'payment_instructions': INVOICE_CONFIG['payment_instructions'],
        }

        os.makedirs('invoices', exist_ok=True)
        filename = f"invoices/{inv_num}.pdf"
        generate_invoice_pdf(filename, data)

        conn = sqlite3.connect('oman_addresses.db')
        c = conn.cursor()
        c.execute('INSERT INTO invoices (invoice_number,partner_name,api_key,billing_period,lookups,deliveries_verified,rate_per_lookup,subtotal,tax,total,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
            (inv_num, partner['partner_name'], partner['api_key'], billing_period, lookups, dv, rate, subtotal, 0, subtotal, now.isoformat()))
        conn.commit()
        conn.close()

        return FileResponse(filename, media_type='application/pdf', filename=f"Wasul-Invoice-{inv_num}.pdf")
    except HTTPException: raise
    except ImportError: raise HTTPException(status_code=500, detail="Invoice generator not available. Ensure invoice_generator.py and reportlab are installed.")
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/invoice-download/{invoice_number}")
async def download_existing_invoice(invoice_number: str):
    filepath = f"invoices/{invoice_number}.pdf"
    if not os.path.exists(filepath): raise HTTPException(status_code=404, detail="Invoice PDF not found.")
    return FileResponse(filepath, media_type='application/pdf', filename=f"Wasul-Invoice-{invoice_number}.pdf")

@app.post("/api/invoice/{invoice_id}/mark-paid")
async def mark_invoice_paid(invoice_id: int):
    conn = sqlite3.connect('oman_addresses.db')
    c = conn.cursor()
    c.execute('UPDATE invoices SET status=? WHERE id=?', ('paid', invoice_id))
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")
    conn.commit()
    conn.close()
    return {"success": True, "message": "Invoice marked as paid"}

# ============================================================
# ROUTES — ADMIN DASHBOARD
# ============================================================

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    try:
        conn = sqlite3.connect('oman_addresses.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM addresses ORDER BY created_at DESC'); addresses = c.fetchall()
        c.execute('SELECT * FROM api_keys WHERE active=1'); partners = c.fetchall()
        c.execute('SELECT COUNT(*) FROM addresses'); total_addr = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM addresses WHERE verified=1'); verified = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM deliveries WHERE success=1'); del_count = c.fetchone()[0]
        c.execute('SELECT SUM(lookups_used) FROM api_keys'); lookups = c.fetchone()[0] or 0
        conn.close()

        addr_rows = ""
        for a in addresses:
            st = '<span class="badge verified">Verified</span>' if a['verified'] else '<span class="badge pending">Pending</span>'
            addr_rows += f'<tr><td><strong>{a["address_code"]}</strong></td><td>{a["phone"]}</td><td>{a["area"] or "—"}, {a["city"]}</td><td><a class="map-link" href="https://www.google.com/maps?q={a["latitude"]},{a["longitude"]}" target="_blank">View</a></td><td>{a["delivery_notes"] or "—"}</td><td>{st}</td><td>{a["successful_deliveries"]}</td></tr>'

        partner_rows = ""
        for p in partners:
            rev = p['lookups_used'] * INVOICE_CONFIG['default_rate_per_lookup']
            partner_rows += f'<tr><td><strong>{p["partner_name"]}</strong></td><td><code>{p["api_key"][:24]}...</code></td><td>{p["lookups_used"]}</td><td>${rev:.2f}</td><td><a href="/api/generate-invoice/{p["id"]}" class="btn btn-orange btn-sm">Generate Invoice</a></td></tr>'

        if not addr_rows: addr_rows = '<tr><td colspan="7" class="empty-state">No addresses registered yet</td></tr>'
        if not partner_rows: partner_rows = '<tr><td colspan="5" class="empty-state">No partners registered yet</td></tr>'

        rate = INVOICE_CONFIG['default_rate_per_lookup']
        return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Dashboard — Wasul</title>{PAGE_CSS}</head><body>
        <div class="top-bar"><a href="/" class="top-bar-logo">Wasul API</a><div class="top-bar-nav"><a href="/">Overview</a><a href="/docs">Documentation</a><a href="/admin" class="active">Dashboard</a><a href="/admin/invoices">Invoices</a></div></div>
        <div class="container">
            <h1>Dashboard</h1><p class="subtitle">Overview of registered addresses and delivery partners</p>
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-value">{total_addr}</div><div class="stat-label">Addresses</div></div>
                <div class="stat-card"><div class="stat-value green">{verified}</div><div class="stat-label">Verified</div></div>
                <div class="stat-card"><div class="stat-value">{del_count}</div><div class="stat-label">Deliveries</div></div>
                <div class="stat-card"><div class="stat-value">{len(partners)}</div><div class="stat-label">Partners</div></div>
                <div class="stat-card"><div class="stat-value orange">${lookups * rate:.0f}</div><div class="stat-label">Est. Revenue</div></div>
            </div>
            <div class="card"><h2>Registered Addresses ({total_addr})</h2><div style="overflow-x:auto"><table><thead><tr><th>Code</th><th>Phone</th><th>Location</th><th>Map</th><th>Notes</th><th>Status</th><th>Deliveries</th></tr></thead><tbody>{addr_rows}</tbody></table></div></div>
            <div class="card"><h2>Delivery Partners ({len(partners)})</h2><div style="overflow-x:auto"><table><thead><tr><th>Partner</th><th>API Key</th><th>Lookups</th><th>Revenue</th><th>Invoice</th></tr></thead><tbody>{partner_rows}</tbody></table></div></div>
        </div></body></html>"""
    except Exception as e:
        return f"<html><head><title>Error</title>{PAGE_CSS}</head><body><div class='container'><div class='card'><h2>Error</h2><p>{str(e)}</p></div></div></body></html>"

# ============================================================
# ROUTES — INVOICE HISTORY PAGE
# ============================================================

@app.get("/admin/invoices", response_class=HTMLResponse)
async def admin_invoices():
    try:
        conn = sqlite3.connect('oman_addresses.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM invoices ORDER BY created_at DESC'); invoices = c.fetchall()
        conn.close()

        inv_rows = ""
        for inv in invoices:
            sc = 'paid' if inv['status'] == 'paid' else 'unpaid'
            sl = 'Paid' if inv['status'] == 'paid' else 'Unpaid'
            mp = "" if inv['status'] == 'paid' else f' <a href="#" onclick="markPaid({inv["id"]});return false;" class="btn btn-outline btn-sm">Mark Paid</a>'
            inv_rows += f'<tr><td><strong>{inv["invoice_number"]}</strong></td><td>{inv["partner_name"]}</td><td>{inv["billing_period"]}</td><td>{inv["lookups"]}</td><td>${inv["total"]:.2f}</td><td><span class="badge {sc}">{sl}</span>{mp}</td><td><a href="/api/invoice-download/{inv["invoice_number"]}" class="btn btn-orange btn-sm">Download</a></td></tr>'

        if not inv_rows: inv_rows = '<tr><td colspan="7" class="empty-state">No invoices generated yet. Go to Dashboard to generate one.</td></tr>'

        return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Invoices — Wasul</title>{PAGE_CSS}</head><body>
        <div class="top-bar"><a href="/" class="top-bar-logo">Wasul API</a><div class="top-bar-nav"><a href="/">Overview</a><a href="/docs">Documentation</a><a href="/admin">Dashboard</a><a href="/admin/invoices" class="active">Invoices</a></div></div>
        <div class="container">
            <h1>Invoices</h1><p class="subtitle">Generated invoices and payment status</p>
            <div class="card"><h2>Invoice History</h2><div style="overflow-x:auto"><table><thead><tr><th>Invoice</th><th>Partner</th><th>Period</th><th>Lookups</th><th>Total</th><th>Status</th><th>PDF</th></tr></thead><tbody>{inv_rows}</tbody></table></div></div>
        </div>
        <script>async function markPaid(id){{if(!confirm('Mark this invoice as paid?'))return;const r=await fetch('/api/invoice/'+id+'/mark-paid',{{method:'POST'}});if(r.ok)location.reload();else alert('Error');}}</script>
        </body></html>"""
    except Exception as e:
        return f"<html><head><title>Error</title>{PAGE_CSS}</head><body><div class='container'><div class='card'><h2>Error</h2><p>{str(e)}</p></div></div></body></html>"

# ============================================================
# START
# ============================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
