import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional

PRESETS: List[Dict[str, Any]] = [
    {
        "id": "semiconductor_war",
        "title": "The Billion-Dollar Silicon Siege: Dutch Machines & Taiwan's Shield",
        "category": "Geopolitics & Tech",
        "source": "Global Financial Times & Tech Forum Briefing",
        "summary": "Deep inside a secretive town in the Netherlands, a single company builds extreme ultraviolet machines that print the brainpower of the modern world. Washington, Beijing, and Taipei are in a high-stakes standoff for control.",
        "text": """
Behind closed doors in Veldhoven, the Netherlands, ASML builds the only machines on earth capable of manufacturing advanced 3nm and 2nm semiconductor microchips. Each machine costs over $350 million and requires three Boeing 747s to transport. 

Recently, diplomatic cables revealed escalating pressure between superpowers. While official press releases cite 'national security and supply chain diversification', defense insiders admit that modern AI supercomputers and hypersonic missiles cannot exist without these microscopic wafers etched in Taiwan and manufactured with Dutch lasers. 

Underneath the formal economic summits, an undercover battle of export bans, corporate espionage, and $50-billion subsidies under the CHIPS Act is unfolding. When a single factory in Hsinchu controls 90% of the world's most cutting-edge computing power, any geopolitical tremor can freeze the global economy overnight. Meanwhile, clandestine shell companies and covert logistics routes are reportedly being set up across neutral ports to bypass strict lithography sanctions.
        """
    },
    {
        "id": "upi_revolution",
        "title": "Chai Stalls to Central Banks: The UPI Coup Against Wall Street Cartels",
        "category": "Economy & Fintech",
        "source": "Economic Forum & FinTech Analysis",
        "summary": "How a zero-cost open protocol launched on roadside tea stalls in India disrupted the multi-billion-dollar interchange fees of Visa, Mastercard, and Western Union.",
        "text": """
For decades, global payment rails like Visa, Mastercard, and SWIFT operated an unassailable toll booth on human commerce, pocketing 2% to 4% swipe fees on billions of everyday card swipes. 

Then came an audacious public infrastructure project: UPI (Unified Payments Interface). Designed to be bank-agnostic, instant, and frictionless, it empowered a roadside coconut vendor to accept QR micro-payments without paying a single paisa in transaction penalties. Within half a decade, monthly volume crossed 15 billion transactions, processing over $250 billion every single month.

The plot thickened when sovereign states across Southeast Asia, Europe, and the Middle East began integrating UPI cross-border rails, cutting out traditional remittance syndicates that long exploited migrant workers with 7% transfer cuts. Wall Street financial lobbies and credit rating giants launched quiet campaigns urging regulation and merchant monetization, but the tide had turned: sovereign digital public rails broke the corporate tollbooth forever.
        """
    },
    {
        "id": "lithium_triangle",
        "title": "White Gold Fever: The Shadow War for the Atacama Salt Flats",
        "category": "Energy & Resources",
        "source": "Resource Forum & Mineral Intelligence",
        "summary": "High in the Andean plateaus spanning Chile, Bolivia, and Argentina lies the Lithium Triangle—the battleground for the fuel of the green revolution.",
        "text": """
Spanning the arid salt flats of the Andes mountains, three South American nations hold more than half of the planet's known lithium reserves—the 'white gold' without which no electric vehicle, smartphone, or military drone battery can be built.

While governments broadcast pledges for net-zero emissions and sustainable battery gigafactories, a ruthless scramble for mining concessions has erupted beneath the surface. International mining conglomerates, sovereign wealth funds, and private security contractors are clashing over local water rights, brine extraction permits, and transport corridors to Pacific ports.

Indigenous communities report falling water tables, while national governments debate nationalizing reserves to create a 'Lithium OPEC'. As demand is projected to spike 500% over the next decade, shadow bidding wars and abrupt contract cancellations have turned quiet alpine villages into the frontline of the 21st-century energy war.
        """
    },
    {
        "id": "space_race_privateers",
        "title": "Orbital Monopolies: The Cloak-and-Dagger Battle for Low Earth Orbit",
        "category": "Aerospace & Defense",
        "source": "Defense & Space Policy Journal",
        "summary": "Private billionaire space fleets, anti-satellite testing, and the scramble for orbital real estate and military communication constellations.",
        "text": """
Low Earth Orbit is running out of parking space. With over 6,000 commercial internet satellites already circling just 550 kilometers above our heads, space is no longer a peaceful frontier—it is the ultimate high ground of global intelligence and commerce.

Recent clashes between defense ministries and private aerospace conglomerates highlighted an uncomfortable reality: sovereign military operations now depend almost entirely on commercial broadband constellations owned by volatile private billionaires. 

Behind diplomatic meetings at the United Nations regarding 'space debris protocols', rival superpowers are racing to deploy counter-space jamming technologies, while private launch monopolies quietly dictate launch windows, frequency spectrums, and satellite insurance premiums. Whoever controls the orbit controls both next-generation broadband and the guidance systems of modern warfare.
        """
    }
]

class ScraperService:
    @staticmethod
    def get_presets() -> List[Dict[str, Any]]:
        return PRESETS

    @staticmethod
    def get_preset_by_id(preset_id: str) -> Optional[Dict[str, Any]]:
        for p in PRESETS:
            if p["id"] == preset_id:
                return p
        return None

    @staticmethod
    def extract_from_url(url: str) -> Dict[str, str]:
        """
        Scrapes and extracts article text and title cleanly from a given URL.
        """
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            raise ValueError(f"Failed to fetch URL: {str(e)}")

        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Remove noisy elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "form"]):
            tag.decompose()
            
        # Extract title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        h1 = soup.find("h1")
        if h1 and h1.get_text():
            title = h1.get_text().strip()
            
        # Extract content
        paragraphs = []
        article = soup.find("article") or soup.find("main") or soup.find("div", class_=re.compile(r"article|content|post|story", re.I))
        
        container = article if article else soup.body
        if container:
            for p in container.find_all("p"):
                text = p.get_text().strip()
                if len(text) > 40:  # Skip tiny fragments
                    paragraphs.append(text)
                    
        full_text = "\n\n".join(paragraphs)
        
        if not full_text:
            # Fallback to general text extraction
            full_text = soup.get_text(separator="\n", strip=True)
            # Truncate to reasonable size
            full_text = full_text[:4000]
            
        if not full_text:
            raise ValueError("Could not extract legible article content from this webpage. Please paste the article text directly.")

        return {
            "title": title or "Current Affairs Dispatch",
            "text": full_text[:6000]  # Safe bounds for processing
        }
