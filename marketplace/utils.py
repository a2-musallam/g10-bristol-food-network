"""Utility functions for food miles calculation."""
import math
from decimal import Decimal
import requests
from django.conf import settings


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance between two coordinates using Haversine formula.
    Returns distance in kilometers.
    
    Args:
        lat1, lon1: Latitude and longitude of first point (farm)
        lat2, lon2: Latitude and longitude of second point (customer)
    
    Returns:
        Distance in kilometers
    """
    # Radius of Earth in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def postcode_to_coordinates(postcode):
    """
    Convert UK postcode to latitude/longitude using Open Postcode Geo API.
    Stores result in cache to avoid repeated API calls.
    
    Args:
        postcode: UK postcode (e.g., "BS8 1AA")
    
    Returns:
        Tuple of (latitude, longitude) or None if lookup fails
    """
    from django.core.cache import cache
    
    cache_key = f"postcode_{postcode.replace(' ', '')}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    try:
        # Using Open Postcode Geo API (free, no auth required)
        url = f"https://api.postcodes.io/postcodes/{postcode.replace(' ', '%20')}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 200 and 'result' in data:
                result = {
                    'latitude': data['result']['latitude'],
                    'longitude': data['result']['longitude']
                }
                cache.set(cache_key, result, 86400)  # Cache for 24 hours
                return result
    except Exception as e:
        print(f"Error looking up postcode {postcode}: {e}")
    
    return None


def calculate_distance_between_postcodes(producer_postcode, customer_postcode, 
                                         producer_lat=None, producer_lon=None):
    """
    Calculate distance in kilometers between two UK postcodes.
    If producer coordinates are provided, use them directly.
    Otherwise, look up both postcodes.
    
    Args:
        producer_postcode: Producer's postcode
        customer_postcode: Customer's postcode
        producer_lat: Producer's latitude (optional)
        producer_lon: Producer's longitude (optional)
    
    Returns:
        Decimal distance in kilometers or None if calculation fails
    """
    # Use provided coordinates if available, else look up
    if producer_lat and producer_lon:
        producer_coords = {'latitude': float(producer_lat), 'longitude': float(producer_lon)}
    else:
        producer_coords = postcode_to_coordinates(producer_postcode)
    
    if not producer_coords:
        return None
    
    customer_coords = postcode_to_coordinates(customer_postcode)
    if not customer_coords:
        return None
    
    distance = haversine_distance(
        producer_coords['latitude'], producer_coords['longitude'],
        customer_coords['latitude'], customer_coords['longitude']
    )
    
    return Decimal(str(round(distance, 2)))


def create_food_miles_record(product, customer, customer_postcode, order=None):
    """
    Create or update a FoodMiles record for a product.
    
    Args:
        product: Product instance
        customer: Customer user instance
        customer_postcode: Customer's postcode
        order: Order instance (optional)
    
    Returns:
        FoodMiles instance or None
    """
    from .models import FoodMiles
    
    distance = product.get_food_miles(customer_postcode)
    if distance is None:
        return None
    
    food_miles, created = FoodMiles.objects.update_or_create(
        product=product,
        customer_postcode=customer_postcode,
        customer=customer,
        order=order,
        defaults={'distance_km': distance}
    )
    
    return food_miles


def calculate_total_food_miles(order_items, customer_postcode):
    """
    Calculate total food miles for an order.
    
    Args:
        order_items: List of (product, quantity) tuples or OrderItem instances
        customer_postcode: Customer's postcode
    
    Returns:
        Decimal total food miles
    """
    total_miles = Decimal('0.00')
    
    for item in order_items:
        if hasattr(item, 'product'):  # OrderItem instance
            product = item.product
        else:  # (product, quantity) tuple
            product = item[0]
        
        miles = product.get_food_miles(customer_postcode)
        if miles:
            total_miles += miles
    
    return total_miles
