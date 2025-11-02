"""
Data Scraping Service

Handles:
- Google Maps business data scraping
- LinkedIn profile scraping
- Website data extraction
- Scraped data storage in Zoho CRM
- AI agent processing of scraped data
"""

import logging
import httpx
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ScrapingService:
    """
    Multi-source data scraping service.
    """

    def __init__(self, zoho_crm_service, credits_service, google_maps_api_key: str = None):
        """
        Initialize Scraping Service.

        Args:
            zoho_crm_service: ZohoCRMService instance
            credits_service: CreditsService instance
            google_maps_api_key: Google Maps API key (optional)
        """
        self.zoho_crm = zoho_crm_service
        self.credits_service = credits_service
        self.google_maps_api_key = google_maps_api_key
        logger.info("Scraping Service initialized")

    async def scrape_google_maps(
        self,
        tenant_id: str,
        query: str,
        location: str,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """
        Scrape Google Maps business listings.

        Args:
            tenant_id: Tenant identifier
            query: Search query (e.g., "restaurants")
            location: Location (e.g., "New York, NY")
            max_results: Maximum number of results

        Returns:
            Dict with scraped businesses
        """
        try:
            if not self.google_maps_api_key:
                return {
                    "status": "error",
                    "message": "Google Maps API key not configured"
                }

            # Check credits
            credits_required = max_results * self.credits_service.PRICING["data_scraping"]["google_maps_per_record"]
            has_credits = await self.credits_service.tenant_service.check_credits(tenant_id, credits_required)

            if not has_credits:
                return {
                    "status": "error",
                    "message": f"Insufficient credits. Required: {credits_required:.2f}"
                }

            # Google Places API endpoint
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": f"{query} in {location}",
                "key": self.google_maps_api_key
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                data = response.json()

            if data.get("status") != "OK":
                return {
                    "status": "error",
                    "message": f"Google Maps API error: {data.get('status')}"
                }

            businesses = []
            results = data.get("results", [])[:max_results]

            for place in results:
                # Get detailed place information
                place_details = await self._get_place_details(place["place_id"])

                business = {
                    "name": place.get("name"),
                    "address": place.get("formatted_address"),
                    "place_id": place.get("place_id"),
                    "rating": place.get("rating"),
                    "total_ratings": place.get("user_ratings_total"),
                    "types": place.get("types", []),
                    "phone": place_details.get("phone"),
                    "website": place_details.get("website"),
                    "email": place_details.get("email"),
                    "opening_hours": place_details.get("opening_hours"),
                    "latitude": place["geometry"]["location"]["lat"],
                    "longitude": place["geometry"]["location"]["lng"],
                    "scraped_at": datetime.now(timezone.utc).isoformat()
                }

                businesses.append(business)

                # Store in Zoho CRM
                await self._store_scraped_business(tenant_id, business, "google_maps")

            # Track usage
            await self.credits_service.track_data_scraping(
                tenant_id, "google_maps", len(businesses)
            )

            logger.info(f"Scraped {len(businesses)} Google Maps businesses for {tenant_id}")

            return {
                "status": "success",
                "source": "google_maps",
                "count": len(businesses),
                "data": businesses
            }

        except Exception as e:
            logger.error(f"Error scraping Google Maps: {e}")
            return {"status": "error", "message": str(e)}

    async def _get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get detailed place information."""
        try:
            if not self.google_maps_api_key:
                return {}

            url = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                "place_id": place_id,
                "fields": "formatted_phone_number,website,opening_hours",
                "key": self.google_maps_api_key
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                data = response.json()

            if data.get("status") == "OK":
                result = data.get("result", {})
                return {
                    "phone": result.get("formatted_phone_number"),
                    "website": result.get("website"),
                    "opening_hours": result.get("opening_hours", {}).get("weekday_text"),
                    "email": None  # Not provided by Google API
                }

            return {}

        except Exception as e:
            logger.error(f"Error getting place details: {e}")
            return {}

    async def scrape_linkedin_profiles(
        self,
        tenant_id: str,
        search_query: str,
        max_profiles: int = 10
    ) -> Dict[str, Any]:
        """
        Scrape LinkedIn profiles.

        ⚠️ WARNING: LinkedIn actively blocks scrapers. This is a basic implementation.
        Consider using LinkedIn API or paid services like PhantomBuster.

        Args:
            tenant_id: Tenant identifier
            search_query: LinkedIn search query
            max_profiles: Maximum number of profiles

        Returns:
            Dict with scraped profiles
        """
        try:
            # Check credits
            credits_required = max_profiles * self.credits_service.PRICING["data_scraping"]["linkedin_per_profile"]
            has_credits = await self.credits_service.tenant_service.check_credits(tenant_id, credits_required)

            if not has_credits:
                return {
                    "status": "error",
                    "message": f"Insufficient credits. Required: {credits_required:.2f}"
                }

            logger.warning("LinkedIn scraping is limited. Consider using LinkedIn API or paid services.")

            # For production: Use LinkedIn API or services like PhantomBuster, Apify
            # This is a placeholder implementation

            profiles = []

            # Placeholder: In production, implement proper LinkedIn API integration
            # or use a scraping service

            return {
                "status": "error",
                "message": "LinkedIn scraping requires LinkedIn API or third-party service. Please use PhantomBuster or Apify integration."
            }

        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
            return {"status": "error", "message": str(e)}

    async def scrape_website(
        self,
        tenant_id: str,
        url: str,
        extract_emails: bool = True,
        extract_phones: bool = True,
        extract_links: bool = False
    ) -> Dict[str, Any]:
        """
        Scrape general website data.

        Args:
            tenant_id: Tenant identifier
            url: Website URL
            extract_emails: Whether to extract email addresses
            extract_phones: Whether to extract phone numbers
            extract_links: Whether to extract all links

        Returns:
            Dict with scraped data
        """
        try:
            # Check credits
            credits_required = self.credits_service.PRICING["data_scraping"]["website_per_page"]
            has_credits = await self.credits_service.tenant_service.check_credits(tenant_id, credits_required)

            if not has_credits:
                return {
                    "status": "error",
                    "message": f"Insufficient credits. Required: {credits_required:.2f}"
                }

            # Fetch website content
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                html_content = response.text

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract data
            scraped_data = {
                "url": url,
                "title": soup.title.string if soup.title else None,
                "scraped_at": datetime.now(timezone.utc).isoformat()
            }

            if extract_emails:
                emails = self._extract_emails(html_content)
                scraped_data["emails"] = list(set(emails))

            if extract_phones:
                phones = self._extract_phones(html_content)
                scraped_data["phones"] = list(set(phones))

            if extract_links:
                links = [a.get('href') for a in soup.find_all('a', href=True)]
                scraped_data["links"] = list(set(links))[:50]  # Limit to 50 links

            # Extract text content
            text_content = soup.get_text(separator=' ', strip=True)
            scraped_data["text_preview"] = text_content[:500]  # First 500 chars

            # Store in Zoho CRM
            await self._store_scraped_website(tenant_id, scraped_data)

            # Track usage
            await self.credits_service.track_data_scraping(tenant_id, "website", 1)

            logger.info(f"Scraped website {url} for {tenant_id}")

            return {
                "status": "success",
                "source": "website",
                "data": scraped_data
            }

        except Exception as e:
            logger.error(f"Error scraping website: {e}")
            return {"status": "error", "message": str(e)}

    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails

    def _extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text."""
        # US phone number patterns
        phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 123-456-7890
            r'\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'  # +1-123-456-7890
        ]

        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))

        return phones

    async def _store_scraped_business(
        self,
        tenant_id: str,
        business_data: Dict[str, Any],
        source: str
    ):
        """Store scraped business in Zoho CRM."""
        try:
            # Create record in Zoho CRM custom module
            crm_data = {
                "Business_Name": business_data.get("name"),
                "Address": business_data.get("address"),
                "Phone": business_data.get("phone"),
                "Website": business_data.get("website"),
                "Email": business_data.get("email"),
                "Rating": business_data.get("rating"),
                "Source": source,
                "Tenant_ID": tenant_id,
                "Scraped_Date": business_data.get("scraped_at"),
                "Place_ID": business_data.get("place_id"),
                "Latitude": business_data.get("latitude"),
                "Longitude": business_data.get("longitude")
            }

            await self.zoho_crm.create_record(
                module="Scraped_Businesses",  # Custom module
                data=crm_data
            )

        except Exception as e:
            logger.error(f"Error storing scraped business: {e}")

    async def _store_scraped_website(
        self,
        tenant_id: str,
        website_data: Dict[str, Any]
    ):
        """Store scraped website data in Zoho CRM."""
        try:
            crm_data = {
                "URL": website_data.get("url"),
                "Title": website_data.get("title"),
                "Emails_Found": ", ".join(website_data.get("emails", [])),
                "Phones_Found": ", ".join(website_data.get("phones", [])),
                "Tenant_ID": tenant_id,
                "Scraped_Date": website_data.get("scraped_at")
            }

            await self.zoho_crm.create_record(
                module="Scraped_Websites",  # Custom module
                data=crm_data
            )

        except Exception as e:
            logger.error(f"Error storing scraped website: {e}")

    async def get_scraped_data(
        self,
        tenant_id: str,
        source: str = "all",
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get scraped data for a tenant.

        Args:
            tenant_id: Tenant identifier
            source: Data source filter (google_maps, linkedin, website, all)
            limit: Maximum records to return

        Returns:
            List of scraped records
        """
        try:
            # Query Zoho CRM for scraped data
            # (Implementation depends on module structure)

            return {
                "status": "success",
                "source": source,
                "count": 0,
                "data": []
            }

        except Exception as e:
            logger.error(f"Error getting scraped data: {e}")
            return {"status": "error", "message": str(e)}

    async def process_scraped_data_with_agent(
        self,
        tenant_id: str,
        task: str,
        data_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Process scraped data with AI agent.

        Args:
            tenant_id: Tenant identifier
            task: Task description (e.g., "extract all emails", "find phone numbers")
            data_ids: List of scraped data record IDs

        Returns:
            Processing result
        """
        try:
            # Get scraped data from Zoho CRM
            # Pass to AI agent for processing
            # Return extracted information

            logger.info(f"Processing scraped data for {tenant_id}: {task}")

            return {
                "status": "success",
                "task": task,
                "records_processed": len(data_ids),
                "result": "Placeholder - integrate with AI agent"
            }

        except Exception as e:
            logger.error(f"Error processing scraped data: {e}")
            return {"status": "error", "message": str(e)}
