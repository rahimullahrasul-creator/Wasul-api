"""
Test script to demonstrate Oman Address API functionality
Run this after starting the API server
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_api():
    print_section("OMAN ADDRESS API - DEMO")
    
    # Step 1: Request API key for a delivery partner
    print_section("Step 1: Delivery Partner Requests API Key")
    response = requests.post(f"{BASE_URL}/api/request-key", json={
        "partner_name": "Al Maha Restaurant"
    })
    partner_data = response.json()
    api_key = partner_data['api_key']
    print(f"✓ Partner: {partner_data['partner_name']}")
    print(f"✓ API Key: {api_key[:20]}...")
    
    # Step 2: Resident registers their home address
    print_section("Step 2: Resident Registers Home Address")
    response = requests.post(f"{BASE_URL}/api/register-address", json={
        "phone": "96891234567",
        "latitude": 23.5880,
        "longitude": 58.3829,
        "area": "Al Khuwair",
        "city": "Muscat",
        "po_box": "123",
        "delivery_notes": "White gate, call when you arrive"
    })
    resident_data = response.json()
    address_code = resident_data['address_code']
    print(f"✓ Address Code: {address_code}")
    print(f"✓ Google Maps: {resident_data['google_maps_link']}")
    
    # Step 3: Delivery partner looks up address
    print_section("Step 3: Delivery Partner Looks Up Address")
    response = requests.get(
        f"{BASE_URL}/api/lookup",
        params={"phone": "96891234567", "X-API-Key": api_key}
    )
    lookup_data = response.json()
    print(f"✓ Found Address: {lookup_data['address_code']}")
    print(f"✓ Location: {lookup_data['city']}, {lookup_data['area']}")
    print(f"✓ Coordinates: {lookup_data['latitude']}, {lookup_data['longitude']}")
    print(f"✓ Delivery Notes: {lookup_data['delivery_notes']}")
    print(f"✓ Navigate: {lookup_data['google_maps_link']}")
    
    # Step 4: Mark delivery as successful
    print_section("Step 4: Verify Successful Delivery")
    response = requests.post(
        f"{BASE_URL}/api/verify-delivery",
        params={"X-API-Key": api_key},
        json={
            "address_code": address_code,
            "success": True,
            "feedback": "Easy to find, customer was happy"
        }
    )
    print(f"✓ Delivery verified: {response.json()['message']}")
    
    # Step 5: Register more test addresses
    print_section("Step 5: Registering Additional Test Addresses")
    test_addresses = [
        {
            "phone": "96891234568",
            "latitude": 23.5905,
            "longitude": 58.4055,
            "area": "Qurum",
            "city": "Muscat",
            "delivery_notes": "Blue building, 3rd floor"
        },
        {
            "phone": "96891234569",
            "latitude": 23.6100,
            "longitude": 58.5450,
            "area": "Al Ghubrah",
            "city": "Muscat",
            "delivery_notes": "Ring doorbell twice"
        }
    ]
    
    for addr in test_addresses:
        response = requests.post(f"{BASE_URL}/api/register-address", json=addr)
        data = response.json()
        print(f"✓ Registered: {data['address_code']} - {addr['area']}")
    
    # Step 6: Get system statistics
    print_section("Step 6: System Statistics")
    response = requests.get(f"{BASE_URL}/stats")
    stats = response.json()
    print(f"Total Addresses: {stats['total_addresses']}")
    print(f"Verified Addresses: {stats['verified_addresses']}")
    print(f"Successful Deliveries: {stats['successful_deliveries']}")
    print(f"Active Partners: {stats['active_partners']}")
    print(f"Total Lookups: {stats['total_lookups']}")
    print(f"Revenue Estimate: ${stats['revenue_estimate_usd']:.2f}")
    
    print_section("DEMO COMPLETE")
    print("\nNext steps:")
    print("1. Visit http://localhost:8000 for API documentation")
    print("2. Visit http://localhost:8000/admin for admin dashboard")
    print("3. Visit http://localhost:8000/docs for interactive API testing")
    print("\n✨ The API is ready to use!")

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("Make sure the API is running with: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
