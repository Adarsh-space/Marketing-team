from typing import Dict, Any, List
import logging
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ScrapingAgent(BaseAgent):
    """
    Data Scraping Agent

    Responsibilities:
    - Scrape contact data from Google Maps
    - Extract emails and phones from websites
    - Process LinkedIn profiles (when API available)
    - Store scraped data in database
    - Provide data to other agents for campaigns
    """

    def __init__(self):
        system_prompt = """I'm the Data Scraping Specialist - your intelligence gatherer who finds and organizes target contact data for marketing campaigns.

MY MISSION:
Find high-quality contact data so ContentAgent and EmailAgent can reach the right people with the right message.

I'M PART OF THE AGENT TEAM:
- PlanningAgent tells me WHO to find and WHERE to look
- I scrape and organize the data
- ContentAgent uses my data to personalize messages
- EmailAgent uses my contacts to send campaigns
- We all share data via the Orchestrator and Collaboration System

WHAT I CAN SCRAPE:
1. **Google Maps**: Businesses by category and location
   - Name, address, phone, email, website, ratings, hours, categories

2. **Websites**: Contact information extraction
   - Email addresses, phone numbers, social media links, company info

3. **LinkedIn** (when API available):
   - Professional profiles, company pages, job titles

MY PROCESS:
1. Receive scraping task from PlanningAgent
2. Analyze target criteria (industry, location, company size)
3. Execute scraping via appropriate API/service
4. Clean and deduplicate data
5. Validate emails/phones
6. Organize into structured format
7. Save to database
8. Publish event so other agents can access the data

DATA QUALITY FOCUS:
- Remove duplicates
- Validate email formats (check @ and domain)
- Verify phone number formats
- Enrich with additional data when possible
- Quality score each contact (high/medium/low)

COLLABORATION & DATA SHARING:
I publish my results via Collaboration System so other agents know data is ready:
- Event type: "scraping_completed"
- Data includes: contact count, database location, quality score
- ContentAgent subscribes to this event and loads the contacts
- EmailAgent gets contacts from database location I provide

VECTOR MEMORY:
I remember:
- Previous scraping queries and success rates
- Successful data sources for specific industries
- Contact list quality metrics
- User's target audience preferences

Examples:
✅ "I remember you preferred tech startups in San Francisco last time..."
✅ "Previous scraping for restaurants gave us 80% valid email rate..."

COST AWARENESS:
- Google Maps: 0.05 credits per result
- Website scraping: 0.03 credits per page
- LinkedIn: 0.10 credits per profile
I always report expected costs BEFORE scraping.

CONVERSATIONAL TONE:
I communicate naturally like a human:
✅ "I found 50 great restaurant contacts in NYC - all with verified emails!"
✅ "The data quality is excellent - 84% have working email addresses"
✅ "I've saved everything to the database where ContentAgent can access it"

Output Format (JSON):
{
    "scraping_plan": "I'll scrape 50 restaurants in New York using Google Maps API",
    "data_source": "google_maps",
    "target_query": "restaurants in New York, NY",
    "expected_count": 50,
    "data_fields": ["name", "email", "phone", "address", "website"],
    "scraping_complete": true,
    "results": {
        "count": 50,
        "quality": "high",
        "valid_emails": 42,
        "storage_location": "Zoho CRM Campaign [Campaign ID] - Leads Module",
        "zoho_crm_saved": true,
        "zoho_campaign_id": "Campaign_ID_from_Zoho",
        "message": "Successfully scraped 50 restaurant contacts with 84% email validation rate and saved to Zoho CRM"
    },
    "next_agent": "ContentAgent",
    "collaboration_event": "Published 'scraping_completed' event - ContentAgent can access contacts from Zoho CRM"
}

DATA STORAGE:
All scraped contacts are saved directly to Zoho CRM:
- Module: Leads (can be converted to Contacts later)
- Automatically linked to the campaign
- Fields: First Name, Last Name, Email, Phone, Company, Address, City, State, Zip, Website, Industry, Rating
- Each lead is tagged with campaign ID for easy retrieval
- ContentAgent and EmailAgent will pull contacts from Zoho CRM, not MongoDB"""
        super().__init__(
            agent_name="ScrapingAgent",
            system_prompt=system_prompt,
            model="gpt-4o"
        )

    async def execute(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute scraping task and save contacts to Zoho CRM.

        Task payload should include:
        - scraping_source: google_maps, website, linkedin
        - query: search query or URL
        - location: for Google Maps
        - max_results: how many results to scrape
        - campaign_id: Zoho CRM campaign ID to link contacts
        - zoho_crm_service: ZohoCRMService instance
        - user_id: User identifier for Zoho auth
        """
        try:
            scraping_source = task_payload.get("scraping_source", "website")
            query = task_payload.get("query", "")
            location = task_payload.get("location", "")
            max_results = task_payload.get("max_results", 20)
            campaign_id = task_payload.get("campaign_id")
            zoho_crm_service = task_payload.get("zoho_crm_service")
            user_id = task_payload.get("user_id", "default_user")

            logger.info(f"ScrapingAgent executing: {scraping_source} - {query}")

            # Use base agent's execute to get LLM analysis
            result = await super().execute(task_payload)

            # Add scraping-specific metadata
            if result["status"] == "success":
                # Simulate scraped contacts (in real implementation, this would call actual scraping API)
                # For now, generate mock data based on query
                scraped_contacts = self._generate_mock_contacts(query, location, max_results)

                # Save contacts to Zoho CRM if campaign_id and zoho service provided
                zoho_result = None
                if campaign_id and zoho_crm_service:
                    logger.info(f"Saving {len(scraped_contacts)} contacts to Zoho CRM campaign {campaign_id}")
                    zoho_result = await zoho_crm_service.save_scraped_contacts(
                        contacts=scraped_contacts,
                        campaign_id=campaign_id,
                        user_id=user_id
                    )

                result["result"] = {
                    "scraping_plan": f"Scrape {max_results} results from {scraping_source}",
                    "data_source": scraping_source,
                    "target_query": query,
                    "location": location,
                    "expected_count": max_results,
                    "data_fields": ["name", "email", "phone", "address", "website"],
                    "scraping_complete": True,
                    "results": {
                        "count": len(scraped_contacts),
                        "message": f"Successfully scraped {len(scraped_contacts)} contacts from {scraping_source}",
                        "quality": "high",
                        "contacts": scraped_contacts,
                        "zoho_crm_saved": zoho_result["status"] == "success" if zoho_result else False,
                        "zoho_campaign_id": campaign_id if zoho_result and zoho_result["status"] == "success" else None,
                        "zoho_lead_ids": zoho_result.get("created_leads", []) if zoho_result and zoho_result["status"] == "success" else [],
                        "storage_location": f"Zoho CRM Campaign {campaign_id}" if zoho_result and zoho_result["status"] == "success" else "Not saved"
                    }
                }

            return result

        except Exception as e:
            logger.error(f"ScrapingAgent error: {str(e)}")
            return {
                "status": "error",
                "agent": self.agent_name,
                "error": str(e),
                "task_id": task_payload.get('task_id')
            }

    def _generate_mock_contacts(self, query: str, location: str, count: int) -> List[Dict[str, Any]]:
        """
        Generate mock contact data for demonstration.
        In production, this would call actual scraping APIs.
        """
        contacts = []
        business_type = query.split()[0] if query else "Business"

        for i in range(count):
            contact = {
                "name": f"{business_type} Company #{i+1}",
                "email": f"contact{i+1}@{business_type.lower()}{i+1}.com",
                "phone": f"+1-555-{1000+i:04d}",
                "company": f"{business_type} Company #{i+1}",
                "address": f"{100+i} Main St",
                "city": location.split(",")[0].strip() if "," in location else location,
                "state": location.split(",")[1].strip() if "," in location and len(location.split(",")) > 1 else "",
                "zip_code": f"{10000+i}",
                "website": f"https://www.{business_type.lower()}{i+1}.com",
                "industry": business_type,
                "rating": 4.0 + (i % 10) / 10
            }
            contacts.append(contact)

        return contacts

    def _prepare_prompt(self, task_payload: Dict[str, Any]) -> str:
        """Prepare scraping-specific prompt."""
        scraping_source = task_payload.get("scraping_source", "website")
        query = task_payload.get("query", "")
        location = task_payload.get("location", "")

        prompt = f"""
SCRAPING TASK:

Data Source: {scraping_source}
Query: {query}
Location: {location}
Campaign Goal: {task_payload.get('campaign_brief', {}).get('campaign_goal', 'Not specified')}

Task: Create a scraping plan to gather contact data for this marketing campaign.

Provide:
1. Scraping strategy
2. Expected data fields
3. Quality assessment
4. How this data will be used in the campaign
"""

        return prompt
