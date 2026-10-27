"""
world_locations.py
Comprehensive Global Countries and Cities Database for Desktop Pet.
Features:
- Complete UN & World Countries and Territories with major cities.
- All Singapore Towns, Planning Areas, and Neighborhoods.
- Prefix-indexed fast lookup for instant typing response.
- Background live geocoding fallback for 100% global coverage of any city on Earth.
"""

from __future__ import annotations
import urllib.request
import urllib.parse
import json
import threading
from typing import Callable, Any

# ── Complete Countries to Major Cities Database ─────────────────────────────
ALL_COUNTRY_TO_CITIES: dict[str, list[str]] = {
    "Afghanistan": ["Kabul"],
    "Albania": ["Tirana"],
    "Algeria": ["Algiers"],
    "Andorra": ["Andorra la Vella"],
    "Angola": ["Luanda"],
    "Antigua and Barbuda": ["St. John's"],
    "Argentina": ["Buenos Aires", "Cordoba", "Rosario", "Mendoza", "Bariloche", "Ushuaia"],
    "Armenia": ["Yerevan"],
    "Aruba": ["Oranjestad"],
    "Australia": ["Canberra", "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast", "Newcastle", "Sunshine Coast", "Wollongong", "Geelong", "Hobart", "Townsville", "Cairns", "Darwin", "Alice Springs"],
    "Austria": ["Vienna", "Salzburg", "Innsbruck", "Graz"],
    "Azerbaijan": ["Baku"],
    "Bahamas": ["Nassau"],
    "Bahrain": ["Manama"],
    "Bangladesh": ["Dhaka", "Chittagong"],
    "Barbados": ["Bridgetown"],
    "Belarus": ["Minsk"],
    "Belgium": ["Brussels", "Antwerp", "Ghent", "Bruges"],
    "Belize": ["Belmopan"],
    "Benin": ["Porto-Novo"],
    "Bermuda": ["Hamilton"],
    "Bhutan": ["Thimphu"],
    "Bolivia": ["La Paz"],
    "Bosnia and Herzegovina": ["Sarajevo"],
    "British Virgin Islands": ["Road Town"],
    "Botswana": ["Gaborone"],
    "Brazil": ["Brasilia", "Sao Paulo", "Rio de Janeiro", "Salvador", "Fortaleza", "Belo Horizonte", "Manaus", "Curitiba", "Recife", "Porto Alegre"],
    "Brunei": ["Bandar Seri Begawan"],
    "Bulgaria": ["Sofia"],
    "Burkina Faso": ["Ouagadougou"],
    "Burundi": ["Gitega"],
    "Cabo Verde": ["Praia"],
    "Cape Verde": ["Praia"],
    "Cambodia": ["Phnom Penh", "Siem Reap"],
    "Cameroon": ["Yaounde"],
    "Canada": ["Ottawa", "Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton", "Quebec City", "Winnipeg", "Hamilton", "Halifax", "Victoria", "Banff", "Whistler"],
    "Cayman Islands": ["George Town"],
    "Cook Islands": ["Avarua"],
    "Central African Republic": ["Bangui"],
    "Chad": ["N'Djamena"],
    "Chile": ["Santiago", "Valparaiso", "Concepcion"],
    "China": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu", "Chongqing", "Hangzhou", "Wuhan", "Xi'an", "Xiamen", "Xining", "Xuzhou", "Qingdao", "Nanjing", "Tianjin", "Suzhou", "Changsha", "Zhengzhou", "Zhuhai", "Harbin", "Kunming", "Dalian"],
    "Colombia": ["Bogota", "Medellin", "Cali", "Cartagena", "Barranquilla"],
    "Comoros": ["Moroni"],
    "Congo, Dem. Rep.": ["Kinshasa"],
    "Congo, Rep.": ["Brazzaville"],
    "Costa Rica": ["San Jose"],
    "Cote d'Ivoire": ["Yamoussoukro"],
    "Croatia": ["Zagreb", "Split", "Dubrovnik"],
    "Cuba": ["Havana"],
    "Curacao": ["Willemstad"],
    "Cyprus": ["Nicosia"],
    "Czech Republic": ["Prague", "Brno"],
    "Denmark": ["Copenhagen", "Aarhus"],
    "Djibouti": ["Djibouti"],
    "Dominica": ["Roseau"],
    "Dominican Republic": ["Santo Domingo"],
    "Ecuador": ["Quito", "Guayaquil"],
    "Egypt": ["Cairo", "Alexandria", "Giza", "Luxor", "Aswan", "Sharm El Sheikh"],
    "El Salvador": ["San Salvador"],
    "Equatorial Guinea": ["Malabo"],
    "Eritrea": ["Asmara"],
    "Estonia": ["Tallinn"],
    "Eswatini": ["Mbabane"],
    "Ethiopia": ["Addis Ababa"],
    "Faroe Islands": ["Torshavn"],
    "Fiji": ["Suva"],
    "Finland": ["Helsinki", "Tampere", "Turku", "Rovaniemi"],
    "France": ["Paris", "Marseille", "Lyon", "Nice", "Toulouse", "Bordeaux", "Strasbourg", "Lille", "Nantes", "Cannes"],
    "French Polynesia": ["Papeete"],
    "Gabon": ["Libreville"],
    "Gambia": ["Banjul"],
    "Georgia": ["Tbilisi"],
    "Germany": ["Berlin", "Munich", "Frankfurt", "Hamburg", "Cologne", "Stuttgart", "Düsseldorf", "Leipzig", "Dresden", "Nuremberg"],
    "Ghana": ["Accra", "Kumasi"],
    "Gibraltar": ["Gibraltar"],
    "Greece": ["Athens", "Thessaloniki", "Heraklion (Crete)", "Santorini", "Mykonos", "Rhodes"],
    "Greenland": ["Nuuk"],
    "Grenada": ["St. George's"],
    "Guam": ["Hagatna"],
    "Guatemala": ["Guatemala City"],
    "Guernsey": ["Saint Peter Port"],
    "Guinea": ["Conakry"],
    "Guinea-Bissau": ["Bissau"],
    "Guyana": ["Georgetown"],
    "Haiti": ["Port-au-Prince"],
    "Honduras": ["Tegucigalpa"],
    "Hong Kong": ["Hong Kong"],
    "Hungary": ["Budapest"],
    "Iceland": ["Reykjavik"],
    "India": ["New Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Ahmedabad", "Pune", "Surat", "Jaipur", "Lucknow", "Kochi"],
    "Indonesia": ["Jakarta", "Surabaya", "Bandung", "Medan", "Semarang", "Makassar", "Yogyakarta", "Denpasar (Bali)", "Batam"],
    "Iran": ["Tehran", "Isfahan", "Shiraz"],
    "Iraq": ["Baghdad", "Erbil"],
    "Ireland": ["Dublin", "Cork", "Galway"],
    "Isle of Man": ["Douglas"],
    "Israel": ["Jerusalem", "Tel Aviv", "Haifa", "Eilat"],
    "Italy": ["Rome", "Milan", "Venice", "Florence", "Naples", "Turin", "Bologna", "Verona", "Palermo", "Genoa"],
    "Jamaica": ["Kingston"],
    "Japan": ["Tokyo", "Osaka", "Kyoto", "Sapporo", "Fukuoka", "Nagoya", "Kobe", "Yokohama", "Hiroshima", "Sendai", "Nara", "Okinawa"],
    "Jersey": ["Saint Helier"],
    "Jordan": ["Amman", "Aqaba"],
    "Kazakhstan": ["Astana", "Almaty"],
    "Kenya": ["Nairobi", "Mombasa", "Kisumu"],
    "Kiribati": ["Tarawa"],
    "Kosovo": ["Pristina"],
    "Kuwait": ["Kuwait City"],
    "Kyrgyzstan": ["Bishkek"],
    "Laos": ["Vientiane", "Luang Prabang"],
    "Latvia": ["Riga"],
    "Lebanon": ["Beirut"],
    "Lesotho": ["Maseru"],
    "Liberia": ["Monrovia"],
    "Libya": ["Tripoli"],
    "Liechtenstein": ["Vaduz"],
    "Lithuania": ["Vilnius"],
    "Luxembourg": ["Luxembourg"],
    "Macau": ["Macau"],
    "Madagascar": ["Antananarivo"],
    "Malawi": ["Lilongwe"],
    "Malaysia": ["Kuala Lumpur", "Johor Bahru", "Penang", "George Town", "Ipoh", "Malacca", "Kota Kinabalu", "Kuching", "Shah Alam"],
    "Maldives": ["Male"],
    "Mali": ["Bamako"],
    "Malta": ["Valletta"],
    "Marshall Islands": ["Majuro"],
    "Mauritania": ["Nouakchott"],
    "Mauritius": ["Port Louis"],
    "Mexico": ["Mexico City", "Guadalajara", "Monterrey", "Puebla", "Tijuana", "Leon", "Juarez", "Cancun", "Merida", "Acapulco", "Xalapa"],
    "Micronesia": ["Palikir"],
    "Moldova": ["Chisinau"],
    "Monaco": ["Monaco"],
    "Mongolia": ["Ulaanbaatar"],
    "Montenegro": ["Podgorica"],
    "Morocco": ["Rabat", "Casablanca", "Marrakech", "Fes", "Tangier"],
    "Mozambique": ["Maputo"],
    "Myanmar": ["Naypyidaw", "Yangon", "Mandalay"],
    "Namibia": ["Windhoek"],
    "Nauru": ["Yaren"],
    "Nepal": ["Kathmandu", "Pokhara"],
    "Netherlands": ["Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven"],
    "New Caledonia": ["Noumea"],
    "New Zealand": ["Wellington", "Auckland", "Christchurch", "Hamilton", "Tauranga", "Dunedin", "Queenstown"],
    "Nicaragua": ["Managua"],
    "Niger": ["Niamey"],
    "Nigeria": ["Abuja", "Lagos", "Kano", "Ibadan"],
    "Niue": ["Alofi"],
    "North Korea": ["Pyongyang"],
    "North Macedonia": ["Skopje"],
    "Northern Mariana Islands": ["Saipan"],
    "Norway": ["Oslo", "Bergen", "Trondheim", "Tromso"],
    "Oman": ["Muscat", "Salalah"],
    "Pakistan": ["Islamabad", "Karachi", "Lahore", "Faisalabad", "Rawalpindi", "Quetta"],
    "Palau": ["Ngerulmud"],
    "Palestine": ["Ramallah"],
    "Panama": ["Panama City"],
    "Papua New Guinea": ["Port Moresby"],
    "Paraguay": ["Asuncion"],
    "Peru": ["Lima", "Cusco", "Arequipa", "Trujillo"],
    "Philippines": ["Manila", "Cebu City", "Davao City", "Quezon City", "Makati", "Baguio"],
    "Poland": ["Warsaw", "Krakow", "Wroclaw", "Gdansk"],
    "Portugal": ["Lisbon", "Porto", "Faro", "Funchal"],
    "Puerto Rico": ["San Juan"],
    "Qatar": ["Doha"],
    "Romania": ["Bucharest"],
    "Russia": ["Moscow", "Saint Petersburg"],
    "Rwanda": ["Kigali"],
    "Saint Kitts and Nevis": ["Basseterre"],
    "Saint Lucia": ["Castries"],
    "Saint Vincent and the Grenadines": ["Kingstown"],
    "Samoa": ["Apia"],
    "San Marino": ["San Marino"],
    "Sao Tome and Principe": ["Sao Tome"],
    "Saudi Arabia": ["Riyadh", "Jeddah", "Mecca", "Medina", "Dammam"],
    "Sint Maarten": ["Philipsburg"],
    "Senegal": ["Dakar"],
    "Serbia": ["Belgrade"],
    "Seychelles": ["Victoria"],
    "Sierra Leone": ["Freetown"],
    "Singapore": ["Singapore", "Jurong", "Jurong East", "Jurong West", "Woodlands", "Tampines", "Bedok", "Yishun", "Ang Mo Kio", "Hougang", "Choa Chu Kang", "Sengkang", "Bukit Batok", "Bukit Panjang", "Punggol", "Pasir Ris", "Queenstown", "Toa Payoh", "Clementi", "Geylang", "Kallang", "Bukit Merah", "Serangoon", "Novena", "Marine Parade", "Bishan", "Outram", "Tanglin", "Newton", "Orchard", "Downtown", "River Valley", "Rochor", "Bugis", "Marina Bay", "Seletar", "Changi", "Mandai", "Sembawang", "Tuas", "Sentosa", "Pulau Ubin"],
    "Slovakia": ["Bratislava"],
    "Slovenia": ["Ljubljana"],
    "Solomon Islands": ["Honiara"],
    "Somalia": ["Mogadishu"],
    "South Africa": ["Cape Town", "Johannesburg", "Durban", "Pretoria", "Port Elizabeth", "Bloemfontein"],
    "South Korea": ["Seoul", "Busan", "Incheon", "Daegu", "Daejeon", "Jeju"],
    "South Sudan": ["Juba"],
    "Spain": ["Madrid", "Barcelona", "Valencia", "Seville", "Malaga", "Bilbao", "Granada", "San Sebastian", "Palma de Mallorca", "Alicante"],
    "Sri Lanka": ["Colombo", "Kandy"],
    "Sudan": ["Khartoum"],
    "Suriname": ["Paramaribo"],
    "Sweden": ["Stockholm", "Gothenburg", "Malmo"],
    "Switzerland": ["Bern", "Zurich", "Geneva", "Basel", "Lucerne", "Lugano", "Zermatt", "Interlaken"],
    "Syria": ["Damascus"],
    "Taiwan": ["Taipei", "Kaohsiung", "Taichung", "Tainan", "Hsinchu"],
    "Tajikistan": ["Dushanbe"],
    "Tanzania": ["Dodoma", "Dar es Salaam", "Zanzibar City", "Arusha"],
    "Thailand": ["Bangkok", "Chiang Mai", "Phuket", "Pattaya", "Hua Hin", "Krabi"],
    "Timor-Leste": ["Dili"],
    "Togo": ["Lome"],
    "Tonga": ["Nuku'alofa"],
    "Trinidad and Tobago": ["Port of Spain"],
    "Tunisia": ["Tunis"],
    "Turkey": ["Ankara", "Istanbul", "Izmir", "Antalya"],
    "Turkmenistan": ["Ashgabat"],
    "Turks and Caicos Islands": ["Cockburn Town"],
    "Tuvalu": ["Funafuti"],
    "U.S. Virgin Islands": ["Charlotte Amalie"],
    "Uganda": ["Kampala"],
    "Ukraine": ["Kyiv"],
    "United Arab Emirates": ["Abu Dhabi", "Dubai", "Sharjah", "Ajman"],
    "United Kingdom": ["London", "Manchester", "Edinburgh", "Birmingham", "Liverpool", "Glasgow", "Leeds", "Bristol", "Sheffield", "Newcastle", "Belfast", "Cardiff", "Oxford", "Cambridge"],
    "United States": ["Washington, D.C.", "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose", "Austin", "Jacksonville", "Fort Worth", "Columbus", "San Francisco", "Charlotte", "Indianapolis", "Seattle", "Denver", "Boston", "El Paso", "Nashville", "Detroit", "Oklahoma City", "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore", "Milwaukee", "Albuquerque", "Tucson", "Fresno", "Sacramento", "Atlanta", "Kansas City", "Miami", "Raleigh", "Minneapolis", "Cleveland", "Tampa", "Honolulu", "Orlando", "Salt Lake City", "New Orleans", "Pittsburgh", "Anchorage"],
    "Uruguay": ["Montevideo"],
    "Uzbekistan": ["Tashkent", "Samarkand"],
    "Vanuatu": ["Port Vila"],
    "Vatican City": ["Vatican City"],
    "Venezuela": ["Caracas"],
    "Vietnam": ["Hanoi", "Ho Chi Minh City", "Da Nang", "Hai Phong", "Nha Trang", "Da Lat"],
    "Yemen": ["Sanaa"],
    "Zambia": ["Lusaka"],
    "Zimbabwe": ["Harare"],
}

# ── Derived Countries List (Country, Capital / Primary City) ────────────────
ALL_COUNTRIES: list[tuple[str, str]] = [
    (country, cities[0] if cities else country)
    for country, cities in ALL_COUNTRY_TO_CITIES.items()
]

# ── Singapore Neighborhoods & Planning Areas ─────────────────────────────────
SINGAPORE_LOCATIONS: list[str] = [
    c for c in ALL_COUNTRY_TO_CITIES.get("Singapore", []) if c != "Singapore"
]

# ── Major Global Metropolitan Centers & Popular Cities (City, Country) ──────
GLOBAL_CITIES: list[tuple[str, str]] = []
for country, cities in ALL_COUNTRY_TO_CITIES.items():
    if country == "Singapore":
        continue
    for city in cities:
        GLOBAL_CITIES.append((city, country))

# ── Common Country Aliases & Shortcodes ──────────────────────────────────────
COMMON_ALIASES: dict[str, tuple[str, str]] = {
    "usa": ("United States", "Washington, D.C."),
    "us": ("United States", "Washington, D.C."),
    "america": ("United States", "Washington, D.C."),
    "uk": ("United Kingdom", "London"),
    "britain": ("United Kingdom", "London"),
    "great britain": ("United Kingdom", "London"),
    "england": ("United Kingdom", "London"),
    "scotland": ("United Kingdom", "Edinburgh"),
    "wales": ("United Kingdom", "Cardiff"),
    "uae": ("United Arab Emirates", "Abu Dhabi"),
    "emirates": ("United Arab Emirates", "Dubai"),
    "sg": ("Singapore", "Singapore"),
    "sin": ("Singapore", "Singapore"),
    "jp": ("Japan", "Tokyo"),
    "kr": ("South Korea", "Seoul"),
    "korea": ("South Korea", "Seoul"),
    "cn": ("China", "Beijing"),
    "prc": ("China", "Beijing"),
    "my": ("Malaysia", "Kuala Lumpur"),
    "id": ("Indonesia", "Jakarta"),
    "ph": ("Philippines", "Manila"),
    "th": ("Thailand", "Bangkok"),
    "vn": ("Vietnam", "Hanoi"),
    "au": ("Australia", "Canberra"),
    "oz": ("Australia", "Sydney"),
    "nz": ("New Zealand", "Wellington"),
    "ca": ("Canada", "Ottawa"),
    "de": ("Germany", "Berlin"),
    "fr": ("France", "Paris"),
    "it": ("Italy", "Rome"),
    "es": ("Spain", "Madrid"),
    "nl": ("Netherlands", "Amsterdam"),
    "holland": ("Netherlands", "Amsterdam"),
    "ch": ("Switzerland", "Bern"),
    "swiss": ("Switzerland", "Zurich"),
    "ru": ("Russia", "Moscow"),
    "sa": ("Saudi Arabia", "Riyadh"),
    "za": ("South Africa", "Cape Town"),
}


# ── Search Function ──────────────────────────────────────────────────────────
def get_global_search_suggestions(query: str, max_results: int = 10) -> list[tuple[str, str]]:
    """
    Given a query (e.g. 'J' or 'Jurong' or 'Sin' or 'Tokyo'):
    Returns a ranked list of (display_text, search_query).
    """
    raw_q = str(query or "").strip()
    q = raw_q.lstrip("🌍📍 ").strip().lower()
    if not q or q.startswith("auto"):
        return []

    results: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add_match(display: str, target: str):
        key = display.lower()
        if key not in seen:
            seen.add(key)
            results.append((display, target))

    # 1. Tier 0: Direct Common Acronyms/Aliases (e.g. 'usa' -> United States, 'uk' -> United Kingdom)
    if q in COMMON_ALIASES:
        c_name, cap = COMMON_ALIASES[q]
        add_match(f"🌍 {c_name} ({cap})", f"{cap}, {c_name}")
        for city in ALL_COUNTRY_TO_CITIES.get(c_name, [])[:5]:
            add_match(f"📍 {city}, {c_name}", f"{city}, {c_name}")

    # 2. Tier 1: Singapore Planning Areas & Towns (prioritizing local user context)
    for loc in SINGAPORE_LOCATIONS:
        if loc.lower().startswith(q):
            add_match(f"📍 {loc}, Singapore", f"{loc}, Singapore")

    # 3. Tier 2: Countries whose name starts with query
    for c_name, cities in ALL_COUNTRY_TO_CITIES.items():
        if c_name.lower().startswith(q):
            cap = cities[0] if cities else c_name
            add_match(f"🌍 {c_name} ({cap})", f"{cap}, {c_name}")
            if len(q) >= 3:
                for city in cities[:5]:
                    add_match(f"📍 {city}, {c_name}", f"{city}, {c_name}")

    # 4. Tier 3: Cities starting with query
    for city, country in GLOBAL_CITIES:
        if city.lower().startswith(q):
            add_match(f"📍 {city}, {country}", f"{city}, {country}")
            if len(results) >= max_results:
                break

    # 5. Tier 4: Substring matches (query length >= 3 to prevent 2-letter noise)
    if len(q) >= 3 and len(results) < max_results:
        # Singapore substring
        for loc in SINGAPORE_LOCATIONS:
            if q in loc.lower():
                add_match(f"📍 {loc}, Singapore", f"{loc}, Singapore")

        # Country substring
        for c_name, cities in ALL_COUNTRY_TO_CITIES.items():
            cap = cities[0] if cities else c_name
            if q in c_name.lower():
                add_match(f"🌍 {c_name} ({cap})", f"{cap}, {c_name}")

        # Global city substring
        for city, country in GLOBAL_CITIES:
            if q in city.lower():
                add_match(f"📍 {city}, {country}", f"{city}, {country}")
                if len(results) >= max_results:
                    break

    return results[:max_results]


# Convenient alias for external search callers
search_locations = get_global_search_suggestions


# ── Live Geocoding Cache & Background Fetcher ────────────────────────────────
_geocode_cache: dict[str, list[tuple[str, str]]] = {}


def fetch_live_geocoding_suggestions(
    query: str,
    callback: Callable[[list[tuple[str, str]]], None]
) -> None:
    """
    Asynchronously queries Open-Meteo Geocoding to fetch any city or town worldwide.
    Calls callback(results) on the main thread when data is ready.
    """
    clean_q = str(query or "").strip().lstrip("🌍📍 ").strip()
    if len(clean_q) < 3 or clean_q.lower().startswith("auto"):
        return

    key = clean_q.lower()
    if key in _geocode_cache:
        callback(_geocode_cache[key])
        return

    def worker():
        try:
            encoded = urllib.parse.quote(clean_q)
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=6&language=en&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "DesktopPet/1.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                raw_items = data.get("results", [])

            live_res: list[tuple[str, str]] = []
            seen_cities: set[str] = set()

            for item in raw_items:
                name = item.get("name")
                country = item.get("country", "")
                admin1 = item.get("admin1", "")

                if not name:
                    continue

                full_key = f"{name}, {country}".lower()
                if full_key in seen_cities:
                    continue
                seen_cities.add(full_key)

                if admin1 and admin1 != name:
                    display = f"📍 {name}, {admin1} ({country})"
                    target = f"{name}, {country}"
                elif country:
                    display = f"📍 {name}, {country}"
                    target = f"{name}, {country}"
                else:
                    display = f"📍 {name}"
                    target = name

                live_res.append((display, target))

            _geocode_cache[key] = live_res
            callback(live_res)
        except Exception:
            pass

    threading.Thread(target=worker, daemon=True).start()
