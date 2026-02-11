
---

# Wasul API

**Address registration and lookup for home delivery in Oman**

Wasul solves a fundamental infrastructure problem: millions of homes in Oman have no street address. Residents rely on P.O. boxes, which means they can't receive food delivery, e-commerce packages, or any home delivery service. Wasul creates a digital addressing layer — residents register their home location once, receive a unique code, and use it anywhere they order.

---

## How It Works

**For Residents:**
Residents visit the registration page, drop a pin on their home location, and receive a unique Wasul code (e.g., OM-MUS-4729A). They use this code whenever they place an order for delivery.

**For Delivery Partners:**
Restaurants and delivery companies use the Wasul API to look up a customer's address by phone number or Wasul code. The API returns exact GPS coordinates, a Google Maps navigation link, and any delivery instructions the resident provided.

---

## API Endpoints

**POST /api/register-address**
Register a new home address. Accepts phone number, GPS coordinates, city, area, and delivery instructions. Returns a unique Wasul code.

**GET /api/lookup**
Look up an address by phone number or Wasul code. Requires an API key. Returns coordinates, Google Maps link, delivery notes, and verification status.

**POST /api/verify-delivery**
Mark a delivery as successful or failed. After three successful deliveries, the address is marked as verified. Requires an API key.

**POST /api/request-key**
Request an API key for delivery partners. Required for lookup and verification endpoints.

---

## Live URLs

- **Landing Page:** https://rahimullahrasul-creator.github.io/Wasul-api/
- **Registration:** https://rahimullahrasul-creator.github.io/Wasul-api/register.html
- **API:** https://oman-address-api.onrender.com
- **API Documentation:** https://oman-address-api.onrender.com/docs
- **Admin Dashboard:** https://oman-address-api.onrender.com/admin

---

## Tech Stack

- **Backend:** Python, FastAPI
- **Database:** SQLite
- **Frontend:** HTML, CSS, JavaScript, Leaflet maps
- **Hosting:** Render (API), GitHub Pages (frontend)

---

## Local Development

```bash
pip install -r requirements.txt
python main.py
```

The API starts at http://localhost:8000. Interactive documentation is available at http://localhost:8000/docs.

---

## Project Files

| File | Purpose |
|------|---------|
| main.py | API server with all endpoints, admin dashboard, and invoice generation |
| invoice_generator.py | PDF invoice generation for delivery partners |
| register.html | Resident-facing address registration page |
| index.html | Public landing page |
| requirements.txt | Python dependencies |
| test_api.py | Automated testing script |
| integration_examples.py | Code samples for delivery partner integration |

---

## Contact

For partnership inquiries or questions, reach out at rahimullahrasul@gmail.com.
