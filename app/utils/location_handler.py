"""
Location handler for approximate map location system.

This module provides functionality to:
1. Geocode street-level addresses using Google Geocoding API
2. Apply deterministic random offsets to coordinates for privacy
3. Return only shifted coordinates (never the real location)
"""

import hashlib
import math
import requests
from functools import lru_cache
from typing import Optional, Dict, Tuple
from app.core.config import GOOGLE_MAPS_API_KEY


@lru_cache(maxsize=256)
def _geocode_cached(full_address: str) -> Optional[Tuple[float, float]]:
    """Cached geocoding lookup. Returns (lat, lng) tuple or None."""
    if not GOOGLE_MAPS_API_KEY:
        return None

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": full_address,
        "key": GOOGLE_MAPS_API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "OK" and data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            return (location["lat"], location["lng"])
    except requests.RequestException as e:
        print(f"Geocoding error: {e}")
    return None


def geocode_address(address: str, city: str, country: str = "Croatia") -> Optional[Dict[str, float]]:
    """
    Geocode an address using Google Geocoding API (cached).
    """
    parts = [p.strip() for p in [address, city, country] if p and p.strip()]
    if not parts:
        return None
    full_address = ", ".join(parts)

    result = _geocode_cached(full_address)
    if result is None:
        return None
    return {"lat": result[0], "lng": result[1]}


def calculate_deterministic_offset(listing_id: str, min_meters: float = 150, max_meters: float = 350) -> Dict[str, float]:
    """
    Calculate a deterministic random offset based on listing ID.
    
    The offset is deterministic - same listing ID always produces the same offset.
    This ensures the approximate location doesn't change on every page load.
    
    Args:
        listing_id: Unique identifier for the listing (used as seed)
        min_meters: Minimum offset distance in meters (default: 150)
        max_meters: Maximum offset distance in meters (default: 350)
    
    Returns:
        Dict with 'distance_meters' and 'angle_degrees' keys
    """
    # Create a hash of the listing ID for deterministic randomness
    hash_bytes = hashlib.sha256(listing_id.encode()).digest()
    
    # Use first 8 bytes for distance, next 8 bytes for angle
    distance_seed = int.from_bytes(hash_bytes[:8], 'big')
    angle_seed = int.from_bytes(hash_bytes[8:16], 'big')
    
    # Normalize to get values in desired ranges
    # Distance: min_meters to max_meters
    distance_range = max_meters - min_meters
    distance_meters = min_meters + (distance_seed % 1000000) / 1000000 * distance_range
    
    # Angle: 0 to 360 degrees
    angle_degrees = (angle_seed % 360000) / 1000
    
    return {
        "distance_meters": distance_meters,
        "angle_degrees": angle_degrees
    }


def apply_geographic_offset(lat: float, lng: float, distance_meters: float, angle_degrees: float) -> Dict[str, float]:
    """
    Apply a geographic offset to coordinates.
    
    Uses proper geographic calculations accounting for Earth's curvature.
    
    Args:
        lat: Original latitude
        lng: Original longitude
        distance_meters: Distance to offset in meters
        angle_degrees: Direction of offset in degrees (0 = North, 90 = East)
    
    Returns:
        Dict with shifted 'lat' and 'lng' values
    """
    # Earth's radius in meters
    EARTH_RADIUS = 6371000
    
    # Convert to radians
    lat_rad = math.radians(lat)
    lng_rad = math.radians(lng)
    angle_rad = math.radians(angle_degrees)
    
    # Angular distance
    angular_distance = distance_meters / EARTH_RADIUS
    
    # Calculate new latitude
    new_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(angular_distance) +
        math.cos(lat_rad) * math.sin(angular_distance) * math.cos(angle_rad)
    )
    
    # Calculate new longitude
    new_lng_rad = lng_rad + math.atan2(
        math.sin(angle_rad) * math.sin(angular_distance) * math.cos(lat_rad),
        math.cos(angular_distance) - math.sin(lat_rad) * math.sin(new_lat_rad)
    )
    
    # Convert back to degrees
    new_lat = math.degrees(new_lat_rad)
    new_lng = math.degrees(new_lng_rad)
    
    return {
        "lat": new_lat,
        "lng": new_lng
    }


def calculate_deterministic_radius(listing_id: str, min_radius: int = 400, max_radius: int = 600) -> int:
    """
    Calculate a deterministic radius based on listing ID.
    
    Args:
        listing_id: Unique identifier for the listing
        min_radius: Minimum radius in meters (default: 400)
        max_radius: Maximum radius in meters (default: 600)
    
    Returns:
        Radius in meters
    """
    # Use a different portion of the hash for radius
    hash_bytes = hashlib.sha256(listing_id.encode()).digest()
    radius_seed = int.from_bytes(hash_bytes[16:24], 'big')
    
    radius_range = max_radius - min_radius
    radius = min_radius + (radius_seed % (radius_range + 1))
    
    return radius


def get_approximate_location(listing_id: str, address: str, city: str, country: str = "Croatia") -> Optional[Dict]:
    """
    Get approximate location for a listing.
    
    This is the main function to use. It:
    1. Geocodes the address
    2. Applies a deterministic random offset (150-350m)
    3. Returns only the shifted coordinates with a radius
    
    The real coordinates are NEVER returned.
    
    Args:
        listing_id: Unique listing identifier (used for deterministic offset)
        address: Street-level address (may be empty)
        city: City name
        country: Country name (default: Croatia)
    
    Returns:
        Dict with 'lat', 'lng', and 'radius' keys, or None if geocoding fails
    """
    # Step 1: Geocode the address (falls back to city-only if address is empty)
    real_coords = geocode_address(address, city, country)
    
    if not real_coords:
        return None
    
    # Step 2: Calculate deterministic offset based on listing ID
    offset = calculate_deterministic_offset(listing_id)
    
    # Step 3: Apply the offset to get shifted coordinates
    shifted_coords = apply_geographic_offset(
        real_coords["lat"],
        real_coords["lng"],
        offset["distance_meters"],
        offset["angle_degrees"]
    )
    
    # Step 4: Calculate deterministic radius
    radius = calculate_deterministic_radius(listing_id)
    
    # Return only shifted coordinates - NEVER the real location
    return {
        "lat": shifted_coords["lat"],
        "lng": shifted_coords["lng"],
        "radius": radius
    }
