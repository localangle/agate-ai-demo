import logging
from typing import Dict, Any, Optional
from agate_utils.geocoding.geocoding_types import GeocodingResult
from agate_utils.geocoding.nominatim import geocode_address

from .point import Point

logger = logging.getLogger(__name__)

########## ADDRESS MODEL ##########

class Address(Point):
    """Model for address-level locations."""

    ########## PRIVATE/HELPER METHODS ##########

    def _prep(self) -> Dict[str, Any]:
        """Prepare address data for geocoding."""
        parts = [self.name]
        if self.city:
            parts.append(self.city)
        if self.state_abbr:
            parts.append(self.state_abbr)
        if self.country:
            parts.append(self.country)
        full_address = ", ".join(parts)

        return {
            "full_address": full_address,
        }

    ########## PUBLIC METHODS ##########

    async def geocode(
        self,
        openai_api_key: Optional[str] = None,
    ) -> Optional[GeocodingResult]:
        """Geocode an address using Nominatim."""
        logger.info("Geocoding address: %s", self.name)

        try:
            prep_data = self._prep()
        except Exception as exc:
            logger.error("Address prep failed for %s: %s", self.name, exc)
            return None

        full_address = prep_data["full_address"]

        # Nominatim
        try:
            result = geocode_address(address=full_address, user_agent="agate-ai-platform/1.0")
            if result and self._is_good_point_result(result):
                logger.info("Nominatim success for %s", self.name)
                self.geocoding_result = result
                return result
        except Exception as exc:
            logger.warning("Nominatim failed for %s: %s", self.name, exc)

        logger.warning("All geocoding services failed for %s", self.name)
        return None
