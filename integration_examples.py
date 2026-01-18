"""
Example Integration Code for Delivery Partners

This shows how restaurants/delivery companies would integrate
the Oman Address API into their systems.
"""

import requests
from typing import Optional, Dict

class OmanAddressClient:
    """
    Client library for Oman Address API
    
    Usage:
        client = OmanAddressClient(api_key="your_api_key_here")
        address = client.lookup_by_phone("96891234567")
        print(f"Navigate to: {address['google_maps_link']}")
    """
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    def lookup_by_phone(self, phone: str) -> Optional[Dict]:
        """
        Look up address by phone number
        
        Args:
            phone: Phone number with country code (e.g., 96891234567)
            
        Returns:
            Dictionary with address details or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/lookup",
                params={"phone": phone, "X-API-Key": self.api_key}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                raise Exception(f"API Error: {response.text}")
                
        except Exception as e:
            print(f"Error looking up address: {str(e)}")
            return None
    
    def lookup_by_code(self, address_code: str) -> Optional[Dict]:
        """
        Look up address by address code
        
        Args:
            address_code: The unique address code (e.g., OM-MUS-4729A)
            
        Returns:
            Dictionary with address details or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/lookup",
                params={"address_code": address_code, "X-API-Key": self.api_key}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                raise Exception(f"API Error: {response.text}")
                
        except Exception as e:
            print(f"Error looking up address: {str(e)}")
            return None
    
    def verify_delivery(self, address_code: str, success: bool, feedback: str = None) -> bool:
        """
        Mark a delivery as successful or failed
        
        Args:
            address_code: The address code used for delivery
            success: True if delivery was successful
            feedback: Optional feedback or issues encountered
            
        Returns:
            True if verification was recorded successfully
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/verify-delivery",
                params={"X-API-Key": self.api_key},
                json={
                    "address_code": address_code,
                    "success": success,
                    "feedback": feedback
                }
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error verifying delivery: {str(e)}")
            return False


# Example 1: Simple restaurant integration
def restaurant_delivery_flow():
    """
    Example: Restaurant receives order and needs to find delivery location
    """
    print("\n=== RESTAURANT DELIVERY FLOW ===\n")
    
    # Initialize client
    client = OmanAddressClient(api_key="omaddr_abc123xyz789")
    
    # Customer places order
    customer_phone = "96891234567"
    order_details = {
        "items": ["Chicken Biryani", "Hummus", "Laban"],
        "total": 12.5,
        "phone": customer_phone
    }
    
    print(f"New order received from: {customer_phone}")
    print(f"Items: {', '.join(order_details['items'])}")
    
    # Look up delivery address
    address = client.lookup_by_phone(customer_phone)
    
    if address:
        print(f"\n✓ Address found!")
        print(f"  Code: {address['address_code']}")
        print(f"  Location: {address['city']}, {address['area']}")
        print(f"  Notes: {address['delivery_notes']}")
        print(f"  Map: {address['google_maps_link']}")
        print(f"  Verified: {'Yes' if address['verified'] else 'No'}")
        
        # Simulate successful delivery
        print("\n[Driver delivers order]")
        success = client.verify_delivery(
            address['address_code'], 
            success=True,
            feedback="Quick delivery, customer was waiting"
        )
        print(f"✓ Delivery verified: {success}")
        
    else:
        print("\n❌ Address not found!")
        print("Suggested action: Call customer for directions or ask them to register at app.omanaddress.com")


# Example 2: E-commerce integration
def ecommerce_checkout_flow():
    """
    Example: E-commerce site during checkout
    """
    print("\n=== E-COMMERCE CHECKOUT FLOW ===\n")
    
    client = OmanAddressClient(api_key="omaddr_xyz789abc123")
    
    # Customer at checkout
    customer_phone = "96891234568"
    
    print(f"Customer checkout initiated: {customer_phone}")
    
    # Check if address exists
    address = client.lookup_by_phone(customer_phone)
    
    if address:
        print(f"\n✓ Delivery address on file:")
        print(f"  {address['area']}, {address['city']}")
        print(f"  {address['delivery_notes']}")
        print("\nProceed with order? [Yes]")
    else:
        print("\n⚠ No delivery address found")
        print("Prompt customer to register address at:")
        print("https://app.omanaddress.com/register")
        print("Or provide address code if they have one")


# Example 3: Address code entry
def address_code_flow():
    """
    Example: Customer provides address code directly
    """
    print("\n=== ADDRESS CODE ENTRY FLOW ===\n")
    
    client = OmanAddressClient(api_key="omaddr_def456ghi789")
    
    # Customer enters their address code
    address_code = "OM-MUS-4729A"
    
    print(f"Customer entered address code: {address_code}")
    
    address = client.lookup_by_code(address_code)
    
    if address:
        print(f"\n✓ Address validated!")
        print(f"  Location: {address['area']}, {address['city']}")
        print(f"  Phone: {address['phone']}")
        print(f"  Deliveries: {address['successful_deliveries']} successful")
        print("\nReady for delivery!")
    else:
        print("\n❌ Invalid address code")
        print("Ask customer to verify the code")


# Example 4: Batch address validation
def batch_validation():
    """
    Example: Validate multiple addresses at once
    """
    print("\n=== BATCH ADDRESS VALIDATION ===\n")
    
    client = OmanAddressClient(api_key="omaddr_batch123")
    
    # List of phone numbers to validate
    phone_numbers = [
        "96891234567",
        "96891234568",
        "96891234569",
        "96899999999"  # This one doesn't exist
    ]
    
    print(f"Validating {len(phone_numbers)} addresses...\n")
    
    valid_count = 0
    for phone in phone_numbers:
        address = client.lookup_by_phone(phone)
        if address:
            valid_count += 1
            print(f"✓ {phone}: {address['area']}, {address['city']}")
        else:
            print(f"❌ {phone}: Not found")
    
    print(f"\nResult: {valid_count}/{len(phone_numbers)} addresses valid")


if __name__ == "__main__":
    print("=" * 60)
    print("  OMAN ADDRESS API - INTEGRATION EXAMPLES")
    print("=" * 60)
    
    # Note: These examples will fail if API isn't running
    # They're meant to show integration patterns
    
    print("\n💡 These are example integration patterns.")
    print("   Update the API keys and base URL for your environment.\n")
    
    # Uncomment to run examples (requires running API server):
    # restaurant_delivery_flow()
    # ecommerce_checkout_flow()
    # address_code_flow()
    # batch_validation()
    
    print("\n" + "=" * 60)
    print("To use this in production:")
    print("1. Get your API key from /api/request-key")
    print("2. Replace 'localhost:8000' with your production URL")
    print("3. Integrate the lookup calls into your order flow")
    print("4. Always verify deliveries to improve data quality")
    print("=" * 60)
