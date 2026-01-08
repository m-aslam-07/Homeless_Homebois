from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable
import asyncio
from functools import partial

from schemas import GeocodeResponse, INDIA_LAT_MIN, INDIA_LAT_MAX, INDIA_LON_MIN, INDIA_LON_MAX

# User-Agent to avoid 403 blocks
USER_AGENT = "logitech_hackathon_fix_v2"

geolocator = Nominatim(user_agent=USER_AGENT, timeout=10)


async def geocode_address(address: str) -> GeocodeResponse:
    """
    Geocode an address to coordinates with India bounds validation.
    Returns coordinates or raises ValueError if outside India bounds.
    """
    try:
        # Run geocoding in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        location = await loop.run_in_executor(
            None,
            partial(geolocator.geocode, address, country_codes="in")
        )
        
        if not location:
            raise ValueError(f"Could not geocode address: {address}")
        
        lat = location.latitude
        lon = location.longitude
        
        # Strict India bounds validation
        if not (INDIA_LAT_MIN <= lat <= INDIA_LAT_MAX):
            raise ValueError(
                f"Latitude {lat} is outside India bounds ({INDIA_LAT_MIN}-{INDIA_LAT_MAX})"
            )
        
        if not (INDIA_LON_MIN <= lon <= INDIA_LON_MAX):
            raise ValueError(
                f"Longitude {lon} is outside India bounds ({INDIA_LON_MIN}-{INDIA_LON_MAX})"
            )
        
        return GeocodeResponse(
            latitude=lat,
            longitude=lon,
            address=location.address or address
        )
    
    except (GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable) as e:
        raise ValueError(f"Geocoding service error: {str(e)}")
    except Exception as e:
        raise ValueError(f"Geocoding failed: {str(e)}")
