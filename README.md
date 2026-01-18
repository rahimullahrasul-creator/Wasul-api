# 🏠 Oman Address API

**Solving Oman's addressing problem - one delivery at a time**

A complete MVP system that enables home address registration and lookup in Oman, where traditional street addressing doesn't exist. This allows delivery companies, restaurants, and e-commerce platforms to deliver to homes that only have P.O. boxes.

---

## 🎯 The Problem

In Oman, many homes don't have street addresses. Residents rely on P.O. boxes, which means:
- ❌ Can't order food delivery to home
- ❌ Can't receive e-commerce packages at home
- ❌ Must drive to post office for every delivery
- ❌ Limited access to online services

**This API solves that.**

---

## 💡 How It Works

### For Residents:
1. Register their home location once
2. Get a unique address code (e.g., `OM-MUS-4729A`)
3. Use this code when ordering anything online
4. Deliveries come straight to their door

### For Delivery Partners:
1. Customer provides phone number or address code
2. API returns exact GPS coordinates + delivery notes
3. Driver navigates directly to the location
4. Verify delivery to improve data quality

---

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API server
python main.py
```

The API will start on `http://localhost:8000`

### Test the System

```bash
# In a new terminal, run the demo
python test_api.py
```

This will:
- Create a test delivery partner
- Register test addresses
- Perform lookups
- Verify deliveries
- Show statistics

---

## 📡 API Endpoints

### 1. Register Address
**POST** `/api/register-address`

Residents use this to add their home location.

```json
{
  "phone": "96891234567",
  "latitude": 23.5880,
  "longitude": 58.3829,
  "area": "Al Khuwair",
  "city": "Muscat",
  "po_box": "123",
  "delivery_notes": "White gate, call when you arrive"
}
```

**Response:**
```json
{
  "success": true,
  "address_code": "OM-MUS-4729A",
  "message": "Address registered successfully!",
  "google_maps_link": "https://www.google.com/maps?q=23.5880,58.3829"
}
```

---

### 2. Lookup Address
**GET** `/api/lookup?phone=96891234567&X-API-Key=your_key`

Delivery partners use this to find where to deliver.

**Response:**
```json
{
  "address_code": "OM-MUS-4729A",
  "phone": "96891234567",
  "latitude": 23.5880,
  "longitude": 58.3829,
  "area": "Al Khuwair",
  "city": "Muscat",
  "delivery_notes": "White gate, call when you arrive",
  "google_maps_link": "https://www.google.com/maps?q=23.5880,58.3829",
  "verified": true,
  "successful_deliveries": 5
}
```

---

### 3. Verify Delivery
**POST** `/api/verify-delivery?X-API-Key=your_key`

Mark delivery as successful/failed to improve data quality.

```json
{
  "address_code": "OM-MUS-4729A",
  "success": true,
  "feedback": "Easy to find, customer was happy"
}
```

---

### 4. Request API Key
**POST** `/api/request-key`

Delivery partners request an API key.

```json
{
  "partner_name": "Al Maha Restaurant"
}
```

**Response:**
```json
{
  "success": true,
  "partner_name": "Al Maha Restaurant",
  "api_key": "omaddr_abc123xyz789...",
  "message": "API key generated. Keep this secure!"
}
```

---

## 💻 Integration Examples

### Python Client

```python
import requests

API_KEY = "omaddr_your_key_here"
BASE_URL = "http://your-api-url.com"

# Lookup address
response = requests.get(
    f"{BASE_URL}/api/lookup",
    params={"phone": "96891234567", "X-API-Key": API_KEY}
)

address = response.json()
print(f"Navigate to: {address['google_maps_link']}")

# Verify delivery
requests.post(
    f"{BASE_URL}/api/verify-delivery",
    params={"X-API-Key": API_KEY},
    json={
        "address_code": address['address_code'],
        "success": True
    }
)
```

### JavaScript/Node.js

```javascript
const API_KEY = 'omaddr_your_key_here';
const BASE_URL = 'http://your-api-url.com';

// Lookup address
const response = await fetch(
  `${BASE_URL}/api/lookup?phone=96891234567&X-API-Key=${API_KEY}`
);
const address = await response.json();

console.log(`Navigate to: ${address.google_maps_link}`);
```

See `integration_examples.py` for complete integration patterns.

---

## 📊 Admin Dashboard

Visit `http://localhost:8000/admin` to see:
- All registered addresses
- Active delivery partners
- Lookup statistics
- Revenue tracking

---

## 💰 Business Model

### Revenue Streams:

**1. Per-Lookup Pricing**
- $0.10-0.25 per address lookup
- Charged to delivery partners/restaurants
- Scales automatically with usage

**2. Monthly Subscriptions**
- Small restaurant: $100-200/month (unlimited lookups)
- Medium platform: $500-1000/month
- Large delivery company: $2000+/month

**3. Setup Fees**
- API integration: $500-2000 one-time
- Custom features: Additional pricing

### Example Revenue:

3 restaurants × 50 deliveries/day = 150 lookups/day
- 150 × $0.15 = $22.50/day
- $675/month from just 3 customers
- Scale to 20-30 restaurants = $4-6k/month

---

## 🗺️ Go-to-Market Strategy

### Phase 1: Proof of Concept (Months 1-2)
- Build MVP ✓ (You have this!)
- Manually map 1 neighborhood in Muscat
- Get 100-200 addresses registered
- Focus on one wealthy/expat area

### Phase 2: Early Customers (Months 2-4)
- Approach 5-10 small local restaurants
- Offer free pilot program
- Prove reliability and ease of use
- Get testimonials and case studies

### Phase 3: Scaling (Months 4-8)
- Sign 3-5 paying customers
- Use revenue to hire local mappers
- Expand to more neighborhoods
- Approach larger delivery platforms

### Phase 4: Market Leadership (Months 8-12)
- Partner with Talabat, Careem, or regional players
- Expand to other cities (Salalah, Sohar)
- Build resident-facing mobile app
- Explore government partnerships

---

## 🛠️ Technical Architecture

### Stack:
- **Backend:** FastAPI (Python)
- **Database:** SQLite (easily upgradable to PostgreSQL)
- **Hosting:** Railway, Render, or DigitalOcean ($5-20/month)
- **Maps:** Google Maps API or Mapbox

### Features:
- ✅ Address registration
- ✅ Phone/code lookup
- ✅ Delivery verification
- ✅ Partner API keys
- ✅ Usage tracking (for billing)
- ✅ Admin dashboard
- ✅ Statistics & analytics

### What's NOT Built (Future Enhancements):
- Mobile app for residents
- Mobile app for drivers
- SMS notifications
- Payment processing
- Advanced analytics dashboard
- Multi-language support (Arabic)

---

## 🚧 Next Steps to Launch

### Immediate (Week 1):
1. ✅ Build MVP (Done!)
2. Deploy to cloud hosting (Railway/Render)
3. Get custom domain (omanaddress.com)
4. Create simple landing page

### Short-term (Weeks 2-4):
1. Find local coordinator in Muscat
2. Manually map one neighborhood
3. Create resident registration web form
4. Approach first 3-5 restaurants

### Medium-term (Months 2-3):
1. Get first paying customer
2. Hire local mappers
3. Build mobile apps (optional, can use web)
4. Improve verification system

---

## ⚠️ Critical Challenges

### 1. Boots on the Ground
**Challenge:** You're in Dallas, business is in Oman
**Solution:** 
- Hire local coordinator ($500-1000/month)
- Or find Omani cofounder
- Visit for 2-4 weeks to launch

### 2. Chicken and Egg
**Challenge:** Residents won't register without delivery options, delivery companies won't pay without addresses
**Solution:**
- Focus on ONE neighborhood
- Get 50-100 addresses manually
- Approach restaurants in that area specifically
- Prove value with small pilot

### 3. Trust & Credibility
**Challenge:** Why would people trust a foreign startup with their location?
**Solution:**
- Partner with local business
- Get early testimonials
- Professional branding
- Transparent data policies

### 4. Competition
**Challenge:** Talabat/Careem might solve this internally
**Solution:**
- Start with businesses they don't serve
- Move fast and prove model
- Focus on smaller cities they ignore
- Build moat with data (verified addresses)

---

## 💸 Initial Capital Needed

**Absolute minimum:** $2,000-3,000
- Hosting: $20/month
- Domain: $50/year
- Local coordinator: $500-1000/month
- Manual mapping labor: $500-1000
- Marketing materials: $200-500

**Realistic:** $5,000-10,000 for 3-month runway

---

## 📈 Success Metrics

**Month 1-2:**
- 100 registered addresses
- 1 pilot restaurant

**Month 3-4:**
- 500 registered addresses
- 3-5 paying customers
- $500-1000 MRR

**Month 6:**
- 2,000 registered addresses
- 10-15 paying customers
- $3,000-5,000 MRR

**Month 12:**
- 10,000+ registered addresses
- 30-50 paying customers
- $10,000-20,000 MRR

---

## 📝 License & Usage

This is a working MVP. You can:
- Deploy this as-is
- Modify for your needs
- Use for commercial purposes
- Build a company around it

---

## 🤝 Support

For questions about implementation:
- Check the `/docs` endpoint for interactive API documentation
- See `integration_examples.py` for code samples
- Review `test_api.py` for usage examples

---

## 🎯 Final Thoughts

**This is a real business opportunity.** The technical part is solved (you have working code). The hard parts are:

1. **Execution in Oman** - You need someone on the ground
2. **Getting first customers** - Start small, prove value
3. **Building the database** - Addresses need to be collected

**You can realistically:**
- Get this deployed in 1 week
- Get first addresses mapped in 2-4 weeks
- Get first paying customer in 2-3 months
- Hit $3-5k MRR in 6 months

The market is there. The problem is real. The solution works.

**Now it's about execution.**

Good luck! 🚀
