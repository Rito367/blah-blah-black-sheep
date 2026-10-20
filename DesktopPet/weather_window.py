"""
weather_window.py
A unified Real-Time Weather & World Time dashboard for Desktop Pet.
Combines live weather forecasts, real-time ticking local clocks, global country search (200+ countries),
and companion speech bubble announcements into one beautiful dashboard.
"""

import tkinter as tk
from datetime import datetime, timezone, timedelta
import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Any
import themes
from world_locations import (
    ALL_COUNTRIES,
    get_global_search_suggestions,
    fetch_live_geocoding_suggestions,
)
# ── Comprehensive list of countries, IANA timezone keys, and fallback UTC offsets ──
ALL_TIMEZONES = [
    ("Afghanistan (Kabul)",                  "Asia/Kabul",                      4.5),
    ("Albania (Tirana)",                     "Europe/Tirane",                   1),
    ("Algeria (Algiers)",                    "Africa/Algiers",                  1),
    ("Andorra (Andorra la Vella)",           "Europe/Andorra",                  1),
    ("Angola (Luanda)",                      "Africa/Luanda",                   1),
    ("Antigua and Barbuda (St. John's)",     "America/Antigua",                -4),
    ("Argentina (Buenos Aires)",             "America/Argentina/Buenos_Aires", -3),
    ("Armenia (Yerevan)",                    "Asia/Yerevan",                    4),
    ("Australia (Sydney / Canberra)",        "Australia/Sydney",                10),
    ("Australia (Melbourne)",                "Australia/Melbourne",             10),
    ("Australia (Perth)",                    "Australia/Perth",                 8),
    ("Austria (Vienna)",                     "Europe/Vienna",                   1),
    ("Azerbaijan (Baku)",                    "Asia/Baku",                       4),
    ("Bahamas (Nassau)",                     "America/Nassau",                 -5),
    ("Bahrain (Manama)",                     "Asia/Bahrain",                    3),
    ("Bangladesh (Dhaka)",                   "Asia/Dhaka",                      6),
    ("Barbados (Bridgetown)",                "America/Barbados",               -4),
    ("Belarus (Minsk)",                      "Europe/Minsk",                    3),
    ("Belgium (Brussels)",                   "Europe/Brussels",                 1),
    ("Belize (Belmopan)",                    "America/Belize",                 -6),
    ("Benin (Porto-Novo)",                   "Africa/Porto-Novo",               1),
    ("Bhutan (Thimphu)",                     "Asia/Thimphu",                    6),
    ("Bolivia (La Paz)",                     "America/La_Paz",                 -4),
    ("Bosnia and Herzegovina (Sarajevo)",    "Europe/Sarajevo",                 1),
    ("Botswana (Gaborone)",                  "Africa/Gaborone",                 2),
    ("Brazil (Brasília / São Paulo)",        "America/Sao_Paulo",              -3),
    ("Brunei (Bandar Seri Begawan)",         "Asia/Brunei",                     8),
    ("Bulgaria (Sofia)",                     "Europe/Sofia",                    2),
    ("Burkina Faso (Ouagadougou)",           "Africa/Ouagadougou",              0),
    ("Burundi (Gitega)",                     "Africa/Bujumbura",                2),
    ("Cabo Verde (Praia)",                   "Atlantic/Cape_Verde",            -1),
    ("Cambodia (Phnom Penh)",                "Asia/Phnom_Penh",                 7),
    ("Cameroon (Yaoundé)",                   "Africa/Douala",                   1),
    ("Canada (Toronto / Ottawa)",            "America/Toronto",                -5),
    ("Canada (Vancouver)",                   "America/Vancouver",              -8),
    ("Central African Republic (Bangui)",    "Africa/Bangui",                   1),
    ("Chad (N'Djamena)",                     "Africa/Ndjamena",                 1),
    ("Chile (Santiago)",                     "America/Santiago",               -3),
    ("China (Beijing / Shanghai)",           "Asia/Shanghai",                   8),
    ("Colombia (Bogotá)",                    "America/Bogota",                 -5),
    ("Comoros (Moroni)",                     "Africa/Nairobi",                  3),
    ("Congo, Dem. Rep. (Kinshasa)",          "Africa/Kinshasa",                 1),
    ("Congo, Rep. (Brazzaville)",            "Africa/Brazzaville",              1),
    ("Costa Rica (San José)",                "America/Costa_Rica",             -6),
    ("Côte d'Ivoire (Yamoussoukro)",         "Africa/Abidjan",                  0),
    ("Croatia (Zagreb)",                     "Europe/Zagreb",                   1),
    ("Cuba (Havana)",                        "America/Havana",                 -5),
    ("Cyprus (Nicosia)",                     "Asia/Nicosia",                    2),
    ("Czech Republic (Prague)",              "Europe/Prague",                   1),
    ("Denmark (Copenhagen)",                 "Europe/Copenhagen",               1),
    ("Djibouti (Djibouti)",                  "Africa/Djibouti",                 3),
    ("Dominica (Roseau)",                    "America/Dominica",               -4),
    ("Dominican Republic (Santo Domingo)",   "America/Santo_Domingo",          -4),
    ("Ecuador (Quito)",                      "America/Guayaquil",              -5),
    ("Egypt (Cairo)",                        "Africa/Cairo",                    2),
    ("El Salvador (San Salvador)",           "America/El_Salvador",            -6),
    ("Equatorial Guinea (Malabo)",           "Africa/Malabo",                   1),
    ("Eritrea (Asmara)",                     "Africa/Asmara",                   3),
    ("Estonia (Tallinn)",                    "Europe/Tallinn",                  2),
    ("Eswatini (Mbabane)",                   "Africa/Mbabane",                  2),
    ("Ethiopia (Addis Ababa)",               "Africa/Addis_Ababa",              3),
    ("Fiji (Suva)",                          "Pacific/Fiji",                   12),
    ("Finland (Helsinki)",                   "Europe/Helsinki",                 2),
    ("France (Paris)",                       "Europe/Paris",                    1),
    ("Gabon (Libreville)",                   "Africa/Libreville",               1),
    ("Gambia (Banjul)",                      "Africa/Banjul",                   0),
    ("Georgia (Tbilisi)",                    "Asia/Tbilisi",                    4),
    ("Germany (Berlin)",                     "Europe/Berlin",                   1),
    ("Ghana (Accra)",                        "Africa/Accra",                    0),
    ("Greece (Athens)",                      "Europe/Athens",                   2),
    ("Grenada (St. George's)",               "America/Grenada",                -4),
    ("Guatemala (Guatemala City)",           "America/Guatemala",              -6),
    ("Guinea (Conakry)",                     "Africa/Conakry",                  0),
    ("Guinea-Bissau (Bissau)",               "Africa/Bissau",                   0),
    ("Guyana (Georgetown)",                  "America/Guyana",                 -4),
    ("Haiti (Port-au-Prince)",               "America/Port-au-Prince",         -5),
    ("Honduras (Tegucigalpa)",               "America/Tegucigalpa",            -6),
    ("Hong Kong",                            "Asia/Hong_Kong",                  8),
    ("Hungary (Budapest)",                   "Europe/Budapest",                 1),
    ("Iceland (Reykjavík)",                  "Atlantic/Reykjavik",              0),
    ("India (New Delhi / Kolkata)",          "Asia/Kolkata",                    5.5),
    ("Indonesia (Jakarta)",                  "Asia/Jakarta",                    7),
    ("Indonesia (Bali / Denpasar)",          "Asia/Makassar",                   8),
    ("Iran (Tehran)",                        "Asia/Tehran",                     3.5),
    ("Iraq (Baghdad)",                       "Asia/Baghdad",                    3),
    ("Ireland (Dublin)",                     "Europe/Dublin",                   0),
    ("Israel (Jerusalem)",                   "Asia/Jerusalem",                  2),
    ("Italy (Rome)",                         "Europe/Rome",                     1),
    ("Jamaica (Kingston)",                   "America/Jamaica",                -5),
    ("Japan (Tokyo)",                        "Asia/Tokyo",                      9),
    ("Jordan (Amman)",                       "Asia/Amman",                      3),
    ("Kazakhstan (Astana / Almaty)",         "Asia/Almaty",                     5),
    ("Kenya (Nairobi)",                      "Africa/Nairobi",                  3),
    ("Kiribati (Tarawa)",                    "Pacific/Tarawa",                 12),
    ("Kuwait (Kuwait City)",                 "Asia/Kuwait",                     3),
    ("Kyrgyzstan (Bishkek)",                 "Asia/Bishkek",                    6),
    ("Laos (Vientiane)",                     "Asia/Vientiane",                  7),
    ("Latvia (Riga)",                        "Europe/Riga",                     2),
    ("Lebanon (Beirut)",                     "Asia/Beirut",                     2),
    ("Lesotho (Maseru)",                     "Africa/Maseru",                   2),
    ("Liberia (Monrovia)",                   "Africa/Monrovia",                 0),
    ("Libya (Tripoli)",                      "Africa/Tripoli",                  2),
    ("Liechtenstein (Vaduz)",                "Europe/Vaduz",                    1),
    ("Lithuania (Vilnius)",                  "Europe/Vilnius",                  2),
    ("Luxembourg (Luxembourg)",              "Europe/Luxembourg",               1),
    ("Madagascar (Antananarivo)",            "Africa/Nairobi",                  3),
    ("Malawi (Lilongwe)",                    "Africa/Blantyre",                 2),
    ("Malaysia (Kuala Lumpur)",              "Asia/Kuala_Lumpur",               8),
    ("Maldives (Malé)",                      "Indian/Maldives",                 5),
    ("Mali (Bamako)",                        "Africa/Bamako",                   0),
    ("Malta (Valletta)",                     "Europe/Malta",                    1),
    ("Marshall Islands (Majuro)",            "Pacific/Majuro",                 12),
    ("Mauritania (Nouakchott)",              "Africa/Nouakchott",               0),
    ("Mauritius (Port Louis)",               "Indian/Mauritius",                4),
    ("Mexico (Mexico City)",                 "America/Mexico_City",            -6),
    ("Micronesia (Palikir)",                 "Pacific/Pohnpei",                11),
    ("Moldova (Chișinău)",                   "Europe/Chisinau",                 2),
    ("Monaco",                               "Europe/Monaco",                   1),
    ("Mongolia (Ulaanbaatar)",               "Asia/Ulaanbaatar",                8),
    ("Montenegro (Podgorica)",               "Europe/Podgorica",                1),
    ("Morocco (Rabat)",                      "Africa/Casablanca",               1),
    ("Mozambique (Maputo)",                  "Africa/Maputo",                   2),
    ("Myanmar (Naypyidaw)",                  "Asia/Yangon",                     6.5),
    ("Namibia (Windhoek)",                   "Africa/Windhoek",                 2),
    ("Nauru (Yaren)",                        "Pacific/Nauru",                  12),
    ("Nepal (Kathmandu)",                    "Asia/Kathmandu",                  5.75),
    ("Netherlands (Amsterdam)",              "Europe/Amsterdam",                1),
    ("New Zealand (Auckland / Wellington)",  "Pacific/Auckland",               12),
    ("Nicaragua (Managua)",                  "America/Managua",                -6),
    ("Niger (Niamey)",                       "Africa/Niamey",                   1),
    ("Nigeria (Abuja / Lagos)",              "Africa/Lagos",                    1),
    ("North Korea (Pyongyang)",              "Asia/Pyongyang",                  9),
    ("North Macedonia (Skopje)",             "Europe/Skopje",                   1),
    ("Norway (Oslo)",                        "Europe/Oslo",                     1),
    ("Oman (Muscat)",                        "Asia/Muscat",                     4),
    ("Pakistan (Islamabad)",                 "Asia/Karachi",                    5),
    ("Palau (Ngerulmud)",                    "Pacific/Palau",                   9),
    ("Palestine (Jerusalem / Gaza)",         "Asia/Gaza",                       2),
    ("Panama (Panama City)",                 "America/Panama",                 -5),
    ("Papua New Guinea (Port Moresby)",      "Pacific/Port_Moresby",           10),
    ("Paraguay (Asunción)",                  "America/Asuncion",               -4),
    ("Peru (Lima)",                          "America/Lima",                   -5),
    ("Philippines (Manila)",                 "Asia/Manila",                     8),
    ("Poland (Warsaw)",                      "Europe/Warsaw",                   1),
    ("Portugal (Lisbon)",                    "Europe/Lisbon",                   0),
    ("Qatar (Doha)",                         "Asia/Qatar",                      3),
    ("Romania (Bucharest)",                  "Europe/Bucharest",                2),
    ("Russia (Moscow)",                      "Europe/Moscow",                   3),
    ("Russia (Vladivostok)",                 "Asia/Vladivostok",               10),
    ("Rwanda (Kigali)",                      "Africa/Kigali",                   2),
    ("Saint Kitts and Nevis (Basseterre)",   "America/St_Kitts",               -4),
    ("Saint Lucia (Castries)",               "America/St_Lucia",               -4),
    ("Saint Vincent & Grenadines",           "America/St_Vincent",             -4),
    ("Samoa (Apia)",                         "Pacific/Apia",                   13),
    ("San Marino",                           "Europe/San_Marino",               1),
    ("São Tomé and Príncipe",                "Africa/Sao_Tome",                 0),
    ("Saudi Arabia (Riyadh)",                "Asia/Riyadh",                     3),
    ("Senegal (Dakar)",                      "Africa/Dakar",                    0),
    ("Serbia (Belgrade)",                    "Europe/Belgrade",                 1),
    ("Seychelles (Victoria)",                "Indian/Mahe",                     4),
    ("Sierra Leone (Freetown)",              "Africa/Freetown",                 0),
    ("Singapore",                            "Asia/Singapore",                  8),
    ("Slovakia (Bratislava)",                "Europe/Bratislava",               1),
    ("Slovenia (Ljubljana)",                 "Europe/Ljubljana",                1),
    ("Solomon Islands (Honiara)",            "Pacific/Guadalcanal",            11),
    ("Somalia (Mogadishu)",                  "Africa/Mogadishu",                3),
    ("South Africa (Pretoria / Cape Town)",  "Africa/Johannesburg",             2),
    ("South Korea (Seoul)",                  "Asia/Seoul",                      9),
    ("South Sudan (Juba)",                   "Africa/Juba",                     2),
    ("Spain (Madrid)",                       "Europe/Madrid",                   1),
    ("Sri Lanka (Colombo)",                  "Asia/Colombo",                    5.5),
    ("Sudan (Khartoum)",                     "Africa/Khartoum",                 2),
    ("Suriname (Paramaribo)",                "America/Paramaribo",             -3),
    ("Sweden (Stockholm)",                   "Europe/Stockholm",                1),
    ("Switzerland (Bern / Zurich)",          "Europe/Zurich",                   1),
    ("Syria (Damascus)",                     "Asia/Damascus",                   3),
    ("Taiwan (Taipei)",                      "Asia/Taipei",                     8),
    ("Tajikistan (Dushanbe)",                "Asia/Dushanbe",                   5),
    ("Tanzania (Dodoma)",                    "Africa/Dar_es_Salaam",            3),
    ("Thailand (Bangkok)",                   "Asia/Bangkok",                    7),
    ("Timor-Leste (Dili)",                   "Asia/Dili",                       9),
    ("Togo (Lomé)",                          "Africa/Lome",                     0),
    ("Tonga (Nukuʻalofa)",                   "Pacific/Tongatapu",              13),
    ("Trinidad and Tobago (Port of Spain)",  "America/Port_of_Spain",          -4),
    ("Tunisia (Tunis)",                      "Africa/Tunis",                    1),
    ("Turkey (Ankara / Istanbul)",           "Europe/Istanbul",                 3),
    ("Turkmenistan (Ashgabat)",              "Asia/Ashgabat",                   5),
    ("Tuvalu (Funafuti)",                    "Pacific/Funafuti",               12),
    ("Uganda (Kampala)",                     "Africa/Kampala",                  3),
    ("Ukraine (Kyiv)",                       "Europe/Kyiv",                     2),
    ("United Arab Emirates (Dubai)",         "Asia/Dubai",                      4),
    ("United Kingdom (London)",              "Europe/London",                   0),
    ("United States (New York - EST)",       "America/New_York",               -5),
    ("United States (Chicago - CST)",        "America/Chicago",                -6),
    ("United States (Denver - MST)",         "America/Denver",                 -7),
    ("United States (Los Angeles - PST)",    "America/Los_Angeles",            -8),
    ("United States (Anchorage - AKST)",     "America/Anchorage",              -9),
    ("United States (Honolulu - HST)",       "Pacific/Honolulu",              -10),
    ("Uruguay (Montevideo)",                 "America/Montevideo",             -3),
    ("Uzbekistan (Tashkent)",                "Asia/Tashkent",                   5),
    ("Vanuatu (Port Vila)",                  "Pacific/Efate",                  11),
    ("Vatican City",                         "Europe/Vatican",                  1),
    ("Venezuela (Caracas)",                  "America/Caracas",                -4),
    ("Vietnam (Hanoi)",                      "Asia/Ho_Chi_Minh",                7),
    ("Yemen (Sanaa)",                        "Asia/Aden",                       3),
    ("Zambia (Lusaka)",                      "Africa/Lusaka",                   2),
    ("Zimbabwe (Harare)",                    "Africa/Harare",                   2),
]

# Backward compatibility mappings for legacy entries
_LEGACY_MAP = {
    "Singapore":           ("Asia/Singapore", 8),
    "London":              ("Europe/London", 0),
    "New York":            ("America/New_York", -5),
    "Tokyo":               ("Asia/Tokyo", 9),
    "Sydney":              ("Australia/Sydney", 10),
    "Beijing / Shanghai":  ("Asia/Shanghai", 8),
    "Seoul":               ("Asia/Seoul", 9),
    "Hong Kong":           ("Asia/Hong_Kong", 8),
    "Bangkok":             ("Asia/Bangkok", 7),
    "Jakarta":             ("Asia/Jakarta", 7),
    "Kolkata":             ("Asia/Kolkata", 5.5),
    "Dubai":               ("Asia/Dubai", 4),
    "Moscow":              ("Europe/Moscow", 3),
    "Istanbul":            ("Europe/Istanbul", 3),
    "Nairobi":             ("Africa/Nairobi", 3),
    "Paris":               ("Europe/Paris", 1),
    "Berlin":              ("Europe/Berlin", 1),
    "Reykjavik":           ("Atlantic/Reykjavik", 0),
    "São Paulo":           ("America/Sao_Paulo", -3),
    "Toronto":             ("America/Toronto", -5),
    "Chicago":             ("America/Chicago", -6),
    "Denver":              ("America/Denver", -7),
    "Los Angeles":         ("America/Los_Angeles", -8),
    "Vancouver":           ("America/Vancouver", -8),
    "Anchorage":           ("America/Anchorage", -9),
    "Honolulu":            ("Pacific/Honolulu", -10),
    "Auckland":            ("Pacific/Auckland", 12),
    "Melbourne":           ("Australia/Melbourne", 10),
    "Perth":               ("Australia/Perth", 8),
}

_TZ_MAP = {row[0]: (row[1], row[2]) for row in ALL_TIMEZONES}
_TZ_MAP.update(_LEGACY_MAP)

DEFAULT_CITIES = ["Singapore", "United Kingdom (London)", "United States (New York - EST)", "Japan (Tokyo)", "Australia (Sydney / Canberra)"]

# ── WMO Weather Interpretation Codes ──────────────────────────────────────────
WMO_INFO: dict[int, tuple[str, str, str, str]] = {
    0:  ("Clear Sky", "☀️", "🌙", "Sunny and bright! Perfect time for outdoor fun! 🐾"),
    1:  ("Mainly Clear", "🌤️", "🌤️", "Looking nice and clear today! Enjoy the breeze! ✨"),
    2:  ("Partly Cloudy", "⛅", "⛅", "Pleasant partly cloudy skies! A nice day ahead! ⛅"),
    3:  ("Overcast", "☁️", "☁️", "Gloomy clouds above, but you bring the sunshine! ☁️"),
    45: ("Foggy", "🌫️", "🌫️", "Misty and foggy outside! Take care on the road! 🌫️"),
    48: ("Rime Fog", "🌫️", "🌫️", "Freezing fog outside! Stay safe and warm! ❄️"),
    51: ("Light Drizzle", "🌦️", "🌦️", "A gentle drizzle outside! Light rain jacket time! 🌧️"),
    53: ("Moderate Drizzle", "🌧️", "🌧️", "Drizzling outside! Don't forget an umbrella! ☔"),
    55: ("Dense Drizzle", "🌧️", "🌧️", "Wet drizzle falling! An umbrella is recommended! ☔"),
    56: ("Freezing Drizzle", "🌧️❄️", "🌧️❄️", "Icy drizzle! Watch out for slippery roads! ❄️"),
    57: ("Dense Freezing Drizzle", "🌧️❄️", "🌧️❄️", "Hazardous freezing drizzle! Bundle up! ❄️"),
    61: ("Slight Rain", "🌦️", "🌦️", "Light rain showers! Keep your umbrella handy! ☔"),
    63: ("Moderate Rain", "🌧️", "🌧️", "Rainy day! Stay cozy and dry indoors! 🌧️"),
    65: ("Heavy Rain", "🌧️⚡", "🌧️⚡", "Heavy downpour! Take shelter and stay dry! 🌧️"),
    66: ("Freezing Rain", "🌧️❄️", "🌧️❄️", "Freezing rain! Stay warm and avoid slips! ❄️"),
    67: ("Heavy Freezing Rain", "🌧️❄️", "🌧️❄️", "Severe freezing rain! Stay warm indoors! ❄️"),
    71: ("Slight Snow", "🌨️", "🌨️", "Gentle snowflakes falling! Winter wonderland! ❄️"),
    73: ("Moderate Snow", "❄️", "❄️", "Snowing outside! Bundle up warm in a scarf! 🧣"),
    75: ("Heavy Snow", "❄️☃️", "❄️☃️", "Heavy snowstorm! Stay cozy by the fire! ☃️"),
    77: ("Snow Grains", "🌨️", "🌨️", "Tiny snow grains drifting down! ❄️"),
    80: ("Light Showers", "🌦️", "🌦️", "Passing rain showers! Grab an umbrella! ☔"),
    81: ("Moderate Showers", "🌧️", "🌧️", "Showers outside! Watch out for puddles! 🌧️"),
    82: ("Violent Showers", "⛈️", "⛈️", "Intense downpours! Best to stay inside! ⛈️"),
    85: ("Light Snow Showers", "🌨️", "🌨️", "Passing snow flurries! ❄️"),
    86: ("Heavy Snow Showers", "❄️", "❄️", "Snow showers gusting! Bundle up tight! 🧣"),
    95: ("Thunderstorm", "⛈️", "⛈️", "Thunderstorm warning! Stay safe indoors! ⛈️⚡"),
    96: ("Thunderstorm & Hail", "⛈️⚡", "⛈️⚡", "Thunder & hail storm! Stay safe inside! ⚡"),
    99: ("Heavy Thunderstorm", "⛈️💥", "⛈️💥", "Severe thunderstorm! Hold my paw! 🐾⚡"),
}


def get_wmo_details(code: int, is_day: bool = True) -> tuple[str, str, str]:
    if code in WMO_INFO:
        desc, day_icon, night_icon, advice = WMO_INFO[code]
        icon = day_icon if is_day else night_icon
        return desc, icon, advice
    return "Variable Weather", "🌤️", "Have a wonderful day no matter the weather! ✨"


def get_temperature_advice(temp: float, unit: str) -> str:
    temp_c = temp if unit == "celsius" else (temp - 32) * 5 / 9
    if temp_c >= 33:
        return "It's scorching hot today! Drink plenty of water and stay cool! 🥤🧊"
    elif temp_c <= 7:
        return "Brrr chilly! Wear a warm coat and stay cozy! 🧣☕"
    return ""


# ── Global Country & Capital Mapping ─────────────────────────────────────────
COUNTRY_ALIASES: dict[str, tuple[str, str]] = {
    "us": ("United States", "Washington"),
    "usa": ("United States", "Washington"),
    "united states": ("United States", "Washington"),
    "america": ("United States", "Washington"),
    "uk": ("United Kingdom", "London"),
    "united kingdom": ("United Kingdom", "London"),
    "britain": ("United Kingdom", "London"),
    "great britain": ("United Kingdom", "London"),
    "england": ("United Kingdom", "London"),
    "scotland": ("United Kingdom", "Edinburgh"),
    "korea": ("South Korea", "Seoul"),
    "south korea": ("South Korea", "Seoul"),
    "north korea": ("North Korea", "Pyongyang"),
    "uae": ("United Arab Emirates", "Dubai"),
    "united arab emirates": ("United Arab Emirates", "Dubai"),
    "dubai": ("United Arab Emirates", "Dubai"),
    "russia": ("Russia", "Moscow"),
    "china": ("China", "Beijing"),
    "japan": ("Japan", "Tokyo"),
    "taiwan": ("Taiwan", "Taipei"),
    "hong kong": ("Hong Kong", "Hong Kong"),
    "germany": ("Germany", "Berlin"),
    "france": ("France", "Paris"),
    "italy": ("Italy", "Rome"),
    "spain": ("Spain", "Madrid"),
    "canada": ("Canada", "Ottawa"),
    "australia": ("Australia", "Sydney"),
    "new zealand": ("New Zealand", "Wellington"),
    "vietnam": ("Vietnam", "Hanoi"),
    "thailand": ("Thailand", "Bangkok"),
    "indonesia": ("Indonesia", "Jakarta"),
    "malaysia": ("Malaysia", "Kuala Lumpur"),
    "philippines": ("Philippines", "Manila"),
    "india": ("India", "New Delhi"),
    "singapore": ("Singapore", "Singapore"),
    "netherlands": ("Netherlands", "Amsterdam"),
    "holland": ("Netherlands", "Amsterdam"),
    "switzerland": ("Switzerland", "Bern"),
    "sweden": ("Sweden", "Stockholm"),
    "norway": ("Norway", "Oslo"),
    "finland": ("Finland", "Helsinki"),
    "denmark": ("Denmark", "Copenhagen"),
    "brazil": ("Brazil", "Brasilia"),
    "mexico": ("Mexico", "Mexico City"),
    "argentina": ("Argentina", "Buenos Aires"),
    "egypt": ("Egypt", "Cairo"),
    "south africa": ("South Africa", "Cape Town"),
    "turkey": ("Turkey", "Ankara"),
    "türkiye": ("Turkey", "Ankara"),
    "greece": ("Greece", "Athens"),
    "portugal": ("Portugal", "Lisbon"),
    "ireland": ("Ireland", "Dublin"),
    "poland": ("Poland", "Warsaw"),
    "saudi arabia": ("Saudi Arabia", "Riyadh"),
    "israel": ("Israel", "Jerusalem"),
}

for _row in ALL_TIMEZONES:
    _label = _row[0]
    if "(" in _label and _label.endswith(")"):
        _c_name = _label.split("(")[0].strip()
        _cap = _label.split("(")[1].rstrip(")").split("/")[0].split("-")[0].strip()
        _c_key = _c_name.lower()
        if _c_key not in COUNTRY_ALIASES:
            COUNTRY_ALIASES[_c_key] = (_c_name, _cap)

for _c_name, _cap in ALL_COUNTRIES:
    _c_key = _c_name.lower()
    if _c_key not in COUNTRY_ALIASES:
        COUNTRY_ALIASES[_c_key] = (_c_name, _cap)


def resolve_country_query(query: str) -> str:
    """
    Resolves country names, abbreviations, or 'Country (Capital)' strings
    to an optimal weather search query. Returns the query as-is if it's already a city.
    """
    q_clean = query.strip()
    q_clean = q_clean.lstrip("🌍📍 ").strip()
    if not q_clean:
        return "auto"

    if "(" in q_clean and q_clean.endswith(")"):
        country = q_clean.split("(")[0].strip()
        city_raw = q_clean.split("(")[1].rstrip(")").split("/")[0].split("-")[0].strip()
        return f"{city_raw}, {country}"

    q_lower = q_clean.lower()
    if q_lower in COUNTRY_ALIASES:
        c_name, cap = COUNTRY_ALIASES[q_lower]
        return f"{cap}, {c_name}"

    for c_key, (c_name, cap) in COUNTRY_ALIASES.items():
        if q_lower == c_key or q_lower == c_name.lower():
            return f"{cap}, {c_name}"

    return q_clean


# ── Network Fetcher (Zero API Key) ───────────────────────────────────────────
def fetch_weather_sync(city: str | None, unit: str = "celsius") -> tuple[dict[str, Any] | None, str | None]:
    """
    Fetch live weather data from Open-Meteo and IP-API.
    Returns (data_dict, None) on success or (None, error_message) on failure.
    """
    headers = {"User-Agent": "DesktopPet/1.0 (Python Weather Agent)"}
    lat: float
    lon: float
    display_city: str
    country_name: str

    c_raw = (city or "").strip()
    c_lower = c_raw.lower()
    is_auto = (
        not c_raw
        or c_lower in ("auto", "auto (gps/ip)", "auto (ip)", "my location", "current location", "gps", "ip")
        or "auto" in c_lower
        or "gps" in c_lower
        or "my location" in c_lower
    )

    try:
        if is_auto:
            # Auto-detect location via IP Geolocation with automatic fallback
            try:
                geo_url = "http://ip-api.com/json/?fields=status,message,city,country,lat,lon"
                req = urllib.request.Request(geo_url, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as res:
                    geo_data = json.loads(res.read().decode("utf-8"))
                if geo_data.get("status") == "success":
                    lat = float(geo_data["lat"])
                    lon = float(geo_data["lon"])
                    display_city = geo_data.get("city", "Singapore")
                    country_name = geo_data.get("country", "")
                else:
                    lat, lon = 1.3521, 103.8198
                    display_city, country_name = "Singapore", "Singapore"
            except Exception:
                lat, lon = 1.3521, 103.8198
                display_city, country_name = "Singapore", "Singapore"
        else:
            # Smartly resolve country names to capital/major city
            resolved_search = resolve_country_query(c_raw)
            encoded = urllib.parse.quote(resolved_search)
            search_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=10&language=en&format=json"
            req = urllib.request.Request(search_url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as res:
                search_data = json.loads(res.read().decode("utf-8"))
            results = search_data.get("results")
            if not results and resolved_search != c_raw:
                encoded_raw = urllib.parse.quote(c_raw)
                search_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_raw}&count=10&language=en&format=json"
                req = urllib.request.Request(search_url, headers=headers)
                with urllib.request.urlopen(req, timeout=6) as res:
                    search_data = json.loads(res.read().decode("utf-8"))
                results = search_data.get("results")

            if not results:
                return None, f"Location '{c_raw}' not found."

            # Rank candidates by population & feature significance (capitals/major cities first)
            def rank_score(item_dict: dict) -> int:
                pop = item_dict.get("population") or 0
                feat = item_dict.get("feature_code") or ""
                f_score = 10000000 if feat == "PPLC" else (5000000 if feat.startswith("PPLA") else (2000000 if feat == "PCLI" else 0))
                return f_score + int(pop)

            sorted_candidates = sorted(results, key=rank_score, reverse=True)
            item = sorted_candidates[0]
            lat = float(item["latitude"])
            lon = float(item["longitude"])
            display_city = item.get("name", c_raw)
            country_name = item.get("country", "")

        # Query Open-Meteo forecast endpoint
        temp_param = "&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch" if unit == "fahrenheit" else ""
        forecast_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat:.4f}&longitude={lon:.4f}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m"
            f"&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,weather_code,wind_speed_10m,is_day"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            f"&forecast_days=4"
            f"&timezone=auto{temp_param}"
        )
        f_req = urllib.request.Request(forecast_url, headers=headers)
        with urllib.request.urlopen(f_req, timeout=7) as res:
            weather_data = json.loads(res.read().decode("utf-8"))

        cur = weather_data.get("current", {})
        daily = weather_data.get("daily", {})
        hourly = weather_data.get("hourly", {})

        utc_offset_sec = int(weather_data.get("utc_offset_seconds", 28800))
        tz_name = str(weather_data.get("timezone", "Asia/Singapore"))
        tz_abbrev = str(weather_data.get("timezone_abbreviation", "GMT+8"))

        cur_temp = round(float(cur.get("temperature_2m", 0.0)), 1)
        feels_like = round(float(cur.get("apparent_temperature", cur_temp)), 1)
        humidity = int(cur.get("relative_humidity_2m", 0))
        wind_speed = round(float(cur.get("wind_speed_10m", 0.0)), 1)
        precip = round(float(cur.get("precipitation", 0.0)), 1)
        wmo_code = int(cur.get("weather_code", 0))
        is_day = bool(cur.get("is_day", 1))

        desc, icon, advice = get_wmo_details(wmo_code, is_day)

        extra_temp_advice = get_temperature_advice(cur_temp, unit)
        if extra_temp_advice and wmo_code in (0, 1, 2, 3):
            advice = extra_temp_advice

        h_times = hourly.get("time", [])
        h_temps = hourly.get("temperature_2m", [])
        h_codes = hourly.get("weather_code", [])
        h_precips = hourly.get("precipitation_probability", [])
        h_precip_amounts = hourly.get("precipitation", [])
        h_is_days = hourly.get("is_day", [])
        h_feels = hourly.get("apparent_temperature", [])
        h_humids = hourly.get("relative_humidity_2m", [])
        h_winds = hourly.get("wind_speed_10m", [])

        forecast_list = []
        d_times = daily.get("time", [])
        d_maxs = daily.get("temperature_2m_max", [])
        d_mins = daily.get("temperature_2m_min", [])
        d_codes = daily.get("weather_code", [])
        d_precips = daily.get("precipitation_probability_max", [])

        for i in range(min(3, len(d_times))):
            d_str = d_times[i]
            try:
                dt = datetime.strptime(d_str, "%Y-%m-%d")
                if i == 0:
                    lbl = "Today"
                    sub_lbl = dt.strftime("%d %b")
                elif i == 1:
                    lbl = "Tomorrow"
                    sub_lbl = dt.strftime("%d %b")
                else:
                    lbl = dt.strftime("%A")
                    sub_lbl = dt.strftime("%d %b")
            except Exception:
                lbl = f"Day {i+1}"
                sub_lbl = ""

            code_i = int(d_codes[i]) if i < len(d_codes) else 0
            d_desc, d_icon, d_advice = get_wmo_details(code_i, True)
            f_max = round(float(d_maxs[i]), 1) if i < len(d_maxs) else cur_temp
            f_min = round(float(d_mins[i]), 1) if i < len(d_mins) else cur_temp
            p_prob = int(d_precips[i]) if i < len(d_precips) and d_precips[i] is not None else 0

            # Gather 24 hourly forecasts for this day
            day_hours = []
            for h_idx in range(len(h_times)):
                t_str = h_times[h_idx]
                if t_str.startswith(d_str):
                    try:
                        h_dt = datetime.strptime(t_str, "%Y-%m-%dT%H:%M")
                        hour_val = h_dt.hour
                        label_12 = h_dt.strftime("%I %p").lstrip("0")
                        label_24 = h_dt.strftime("%H:%M")
                    except Exception:
                        hour_val = len(day_hours)
                        label_12 = f"{hour_val}:00"
                        label_24 = f"{hour_val:02d}:00"

                    h_temp = round(float(h_temps[h_idx]), 1) if h_idx < len(h_temps) else cur_temp
                    h_feel = round(float(h_feels[h_idx]), 1) if h_idx < len(h_feels) else h_temp
                    h_code = int(h_codes[h_idx]) if h_idx < len(h_codes) else 0
                    h_day = bool(h_is_days[h_idx]) if h_idx < len(h_is_days) else True
                    h_desc, h_icon, _ = get_wmo_details(h_code, h_day)
                    h_rain = int(h_precips[h_idx]) if h_idx < len(h_precips) and h_precips[h_idx] is not None else 0
                    h_rain_amt = round(float(h_precip_amounts[h_idx]), 1) if h_idx < len(h_precip_amounts) and h_precip_amounts[h_idx] is not None else 0.0
                    h_hum = int(h_humids[h_idx]) if h_idx < len(h_humids) else humidity
                    h_wind = round(float(h_winds[h_idx]), 1) if h_idx < len(h_winds) else wind_speed

                    day_hours.append({
                        "time_str": t_str,
                        "hour": hour_val,
                        "label_12": label_12,
                        "label_24": label_24,
                        "temp": h_temp,
                        "feels_like": h_feel,
                        "weather_code": h_code,
                        "is_day": h_day,
                        "desc": h_desc,
                        "icon": h_icon,
                        "rain_prob": h_rain,
                        "precip": h_rain_amt,
                        "humidity": h_hum,
                        "wind": h_wind,
                    })

            forecast_list.append({
                "day_index": i,
                "date_str": d_str,
                "label": lbl,
                "sub_label": sub_lbl,
                "icon": d_icon,
                "desc": d_desc,
                "advice": d_advice,
                "max": f_max,
                "min": f_min,
                "rain_prob": p_prob,
                "hourly": day_hours,
            })

        unit_sym = "°C" if unit == "celsius" else "°F"
        wind_unit = "km/h" if unit == "celsius" else "mph"
        precip_unit = "mm" if unit == "celsius" else "in"

        result = {
            "city": display_city,
            "country": country_name,
            "lat": lat,
            "lon": lon,
            "utc_offset": utc_offset_sec,
            "tz_name": tz_name,
            "tz_abbrev": tz_abbrev,
            "temp": cur_temp,
            "feels_like": feels_like,
            "humidity": humidity,
            "wind": wind_speed,
            "precip": precip,
            "weather_code": wmo_code,
            "is_day": is_day,
            "unit": unit_sym,
            "wind_unit": wind_unit,
            "precip_unit": precip_unit,
            "desc": desc,
            "icon": icon,
            "advice": advice,
            "forecast": forecast_list,
            "updated_time": datetime.now().strftime("%H:%M"),
        }
        return result, None

    except urllib.error.URLError:
        return None, "Network offline or unreachable."
    except TimeoutError:
        return None, "Connection timed out."
    except Exception as exc:
        return None, f"Error: {exc}"


# ── WeatherWindow GUI Class ──────────────────────────────────────────────────
class WeatherWindow:
    def __init__(
        self,
        root: tk.Tk,
        get_data: Callable[[], dict],
        save_data: Callable[[dict], None],
        on_bubble: Callable[..., Any] | None = None,
        on_menu: Callable[..., Any] | None = None,
    ):
        self.root = root
        self.get_data = get_data
        self.save_data = save_data
        self.on_bubble = on_bubble
        self.on_menu = on_menu

        self.win: tk.Toplevel | None = None
        self.cached_weather: dict[str, Any] | None = None
        self._world_weather_cache: dict[str, dict[str, Any]] = {}
        self._is_fetching: bool = False
        self._dx: int = 0
        self._dy: int = 0

        # Tab State: "weather" or "world_clock"
        self._active_tab: str = "weather"
        self._current_utc_offset: int = 28800  # Default Singapore +8
        self._current_tz_abbrev: str = "GMT+8"
        self._ticker_id: str | None = None

        # UI References
        self._btn_tab_weather: tk.Button | None = None
        self._btn_tab_clock: tk.Button | None = None
        self._body_container: tk.Frame | None = None

        # Tab 1 Widgets
        self._status_lbl: tk.Label | None = None
        self._location_lbl: tk.Label | None = None
        self._live_clock_lbl: tk.Label | None = None
        self._hero_icon_lbl: tk.Label | None = None
        self._hero_temp_lbl: tk.Label | None = None
        self._hero_desc_lbl: tk.Label | None = None
        self._hero_feels_lbl: tk.Label | None = None
        self._metric_humid_val: tk.Label | None = None
        self._metric_wind_val: tk.Label | None = None
        self._metric_precip_val: tk.Label | None = None
        self._metric_range_val: tk.Label | None = None
        self._forecast_cards: list[dict[str, Any]] = []
        self._forecast_card_widgets: list[dict[str, Any]] = []
        self._selected_day_idx: int = 0
        self._selected_hour_idx: int | None = None
        self._hourly_canvas: tk.Canvas | None = None
        self._hourly_frame: tk.Frame | None = None
        self._hourly_sb: tk.Scrollbar | None = None
        self._hourly_card_widgets: list[dict[str, Any]] = []
        self._hourly_title_lbl: tk.Label | None = None
        self._hour_inspector_lbl: tk.Label | None = None
        self._quick_jump_frame: tk.Frame | None = None
        self._say_btn: tk.Button | None = None
        self._pet_advice_lbl: tk.Label | None = None
        self._search_entry: tk.Entry | None = None
        self._btn_c: tk.Button | None = None
        self._btn_f: tk.Button | None = None
        self._canvas: tk.Canvas | None = None
        self._content_id: int | None = None

        # Tab 2 Widgets (World Clock)
        self._clock_rows_frame: tk.Frame | None = None
        self._clock_row_items: list[dict[str, Any]] = []

        # Autocomplete suggestions state
        self._suggest_frame: tk.Frame | None = None
        self._suggest_listbox: tk.Listbox | None = None
        self._suggest_items: list[tuple[str, str]] = []
        self._last_suggest_query: str = ""
        self._toolbar_frame: tk.Frame | None = None

    # ── Visibility & Tab Controls ────────────────────────────────────────────
    def show(self, near_x: int = 200, near_y: int = 200, tab: str = "weather"):
        self._active_tab = tab
        if self.win and self.win.winfo_exists():
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            self._switch_tab(tab)
            return
        self._build(near_x, near_y)
        self._start_clock_ticker()
        self._fetch_weather()

    def show_tab(self, tab: str, near_x: int = 200, near_y: int = 200):
        self.show(near_x, near_y, tab=tab)

    def hide(self):
        self._stop_clock_ticker()
        if self.win and self.win.winfo_exists():
            self.win.destroy()
            self.win = None

    def toggle(self, near_x: int = 200, near_y: int = 200):
        if self.win and self.win.winfo_exists():
            self.hide()
        else:
            self.show(near_x, near_y)

    def apply_theme(self):
        if self.win and self.win.winfo_exists():
            x, y = self.win.winfo_x(), self.win.winfo_y()
            current_tab = self._active_tab
            self.hide()
            self.show(x, y, tab=current_tab)

    # ── Live Clock Ticker ────────────────────────────────────────────────────
    def _start_clock_ticker(self):
        self._stop_clock_ticker()
        self._tick_clock()

    def _stop_clock_ticker(self):
        if self._ticker_id:
            try:
                self.root.after_cancel(self._ticker_id)
            except Exception:
                pass
            self._ticker_id = None

    def _tick_clock(self):
        if not (self.win and self.win.winfo_exists()):
            return

        # 1. Update Tab 1 Live Clock Badge
        tz = timezone(timedelta(seconds=self._current_utc_offset))
        now = datetime.now(tz)
        t_str = now.strftime("%I:%M:%S %p")
        d_str = now.strftime("%a, %d %b %Y")

        if self._live_clock_lbl and self._live_clock_lbl.winfo_exists():
            if self._selected_day_idx == 0:
                self._live_clock_lbl.configure(text=f"⏰ {t_str} • {d_str} ({self._current_tz_abbrev})")

        # 2. Update Tab 2 World Clock Rows
        if self._active_tab == "world_clock" and self._clock_row_items:
            for item in self._clock_row_items:
                time_lbl = item.get("time_lbl")
                date_lbl = item.get("date_lbl")
                off_h = item.get("offset_hours", 0.0)
                if time_lbl and time_lbl.winfo_exists():
                    c_tz = timezone(timedelta(hours=off_h))
                    c_now = datetime.now(c_tz)
                    time_lbl.configure(text=c_now.strftime("%I:%M:%S %p"))
                    if date_lbl and date_lbl.winfo_exists():
                        date_lbl.configure(text=c_now.strftime("%a, %d %b"))

        self._ticker_id = self.root.after(1000, self._tick_clock)

    # ── Speech Bubble Integration (Combined Weather & Time) ──────────────────
    def say_weather_in_bubble(self):
        """Announce current weather combined with local time in desktop pet speech bubble."""
        if not self.on_bubble:
            return

        if self.cached_weather:
            self._broadcast_bubble(self.cached_weather, self._selected_day_idx)
        else:
            data = self.get_data()
            city = data.get("weather_city", "auto")
            unit = data.get("weather_unit", "celsius")

            def worker():
                res, _ = fetch_weather_sync(city, unit)
                if res:
                    self.cached_weather = res
                    self.root.after(0, lambda: self._broadcast_bubble(res, self._selected_day_idx))

            threading.Thread(target=worker, daemon=True).start()

    def _broadcast_bubble(self, data: dict[str, Any], day_idx: int | None = None):
        if not self.on_bubble:
            return
        idx = self._selected_day_idx if day_idx is None else day_idx
        city = data.get("city", "Here")
        unit = data.get("unit", "°C")
        forecast = data.get("forecast", [])

        if idx > 0 and idx < len(forecast):
            f_day = forecast[idx]
            lbl = f_day.get("label", "Tomorrow")
            icon = f_day.get("icon", "🌤️")
            desc = f_day.get("desc", "Forecast")
            f_max = f_day.get("max", "--")
            f_min = f_day.get("min", "--")
            rain_p = f_day.get("rain_prob", 0)
            advice = f_day.get("advice", "Have a wonderful day! ✨")

            bubble_text = (
                f"{icon} {city} • {lbl}'s Weather\n"
                f"{f_max}° / {f_min}° {desc} (💧 {rain_p}% Rain)\n"
                f"{advice}"
            )
        else:
            temp = data.get("temp", "--")
            icon = data.get("icon", "🌤️")
            desc = data.get("desc", "Live Weather")
            feels = data.get("feels_like", temp)
            advice = data.get("advice", "Have a lovely day! ✨")

            # Local time for city
            off_sec = int(data.get("utc_offset", self._current_utc_offset))
            tz = timezone(timedelta(seconds=off_sec))
            now = datetime.now(tz)
            local_time = now.strftime("%I:%M %p").lstrip("0")

            short_advice = advice
            if "!" in short_advice:
                short_advice = short_advice.split("!")[0] + "!"
            elif "." in short_advice:
                short_advice = short_advice.split(".")[0] + "!"

            bubble_text = (
                f"{icon} {city} • {local_time}\n"
                f"{temp}{unit} {desc} (Feels {feels}{unit})\n"
                f"{short_advice}"
            )
        self.on_bubble(bubble_text, play_sound=True)

    # ── Background Data Fetching ─────────────────────────────────────────────
    def _fetch_weather(self, city_override: str | None = None):
        if self._is_fetching:
            return
        self._is_fetching = True

        data = self.get_data()
        city = city_override if city_override is not None else data.get("weather_city", "auto")
        unit = data.get("weather_unit", "celsius")

        if self._status_lbl and self._status_lbl.winfo_exists():
            self._status_lbl.configure(text="⏳ Fetching live weather & time...", fg="#3498db")

        def task():
            result, err = fetch_weather_sync(city, unit)

            def update_ui():
                self._is_fetching = False
                if err:
                    if self._status_lbl and self._status_lbl.winfo_exists():
                        self._status_lbl.configure(text=f"⚠️ {err}", fg="#e74c3c")
                elif result:
                    self.cached_weather = result
                    self._current_utc_offset = int(result.get("utc_offset", 28800))
                    self._current_tz_abbrev = str(result.get("tz_abbrev", "GMT+8"))
                    self._render_weather_data(result)

            self.root.after(0, update_ui)

        threading.Thread(target=task, daemon=True).start()

    def _get_search_suggestions(self, query: str) -> list[tuple[str, str]]:
        """Finds matching countries and cities starting with the typed alphabet / prefix."""
        return get_global_search_suggestions(query, max_results=8)

    def _on_search_key_release(self, event: Any):
        if event.keysym in ("Down", "Up", "Return", "Escape", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"):
            return
        if not self._search_entry:
            return

        raw_q = self._search_entry.get().strip()
        clean_q = raw_q.lstrip("🌍📍 ").strip()
        if not clean_q or clean_q.lower().startswith("auto"):
            self._hide_suggestions()
            return

        self._last_suggest_query = clean_q.lower()
        items = self._get_search_suggestions(clean_q)
        if not items or not self._suggest_listbox:
            self._hide_suggestions()
        else:
            self._suggest_items = list(items)
            self._suggest_listbox.delete(0, tk.END)
            for disp, _ in items:
                self._suggest_listbox.insert(tk.END, f"  {disp}")
            self._show_suggestions()

        # If user typed 3+ letters, asynchronously query live worldwide geocoder
        if len(clean_q) >= 3:
            def _on_live(live_res: list[tuple[str, str]], q: str = clean_q) -> None:
                self.root.after(0, lambda: self._apply_live_suggestions(q, live_res))

            fetch_live_geocoding_suggestions(clean_q, _on_live)

    def _apply_live_suggestions(self, query: str, live_items: list[tuple[str, str]]):
        if not (self._search_entry and self._suggest_listbox and self._suggest_frame):
            return
        curr_q = self._search_entry.get().strip().lstrip("🌍📍 ").strip()
        if curr_q.lower() != query.lower():
            return
        if not live_items:
            return

        existing = {target.lower() for _, target in self._suggest_items}
        added = False
        for disp, target in live_items:
            if target.lower() not in existing:
                existing.add(target.lower())
                self._suggest_items.append((disp, target))
                self._suggest_listbox.insert(tk.END, f"  {disp}")
                added = True
                if len(self._suggest_items) >= 10:
                    break

        if added:
            self._show_suggestions()

    def _show_suggestions(self):
        if not (self._suggest_frame and self._suggest_listbox and self._search_entry and self._toolbar_frame and self._body_container):
            return
        if not (self.win and self.win.winfo_exists()):
            return

        x = 0
        y = self._toolbar_frame.winfo_height() + 2
        w = max(240, self._body_container.winfo_width())
        count = min(8, self._suggest_listbox.size())
        h = max(55, 24 + count * 22)

        self._suggest_frame.place(x=x, y=y, width=w, height=h)
        self._suggest_frame.lift()

    def _hide_suggestions(self):
        if self._suggest_frame and self._suggest_frame.winfo_exists():
            self._suggest_frame.place_forget()
        self._suggest_items = []

    def _on_search_down_arrow(self, event: Any) -> str | None:
        if self._suggest_frame and self._suggest_frame.winfo_ismapped() and self._suggest_listbox and self._suggest_listbox.size() > 0:
            self._suggest_listbox.selection_clear(0, tk.END)
            self._suggest_listbox.selection_set(0)
            self._suggest_listbox.activate(0)
            self._suggest_listbox.focus_set()
            return "break"
        return None

    def _on_suggest_up_arrow(self, event: Any) -> str | None:
        if self._suggest_listbox and self._suggest_listbox.curselection():
            cur = self._suggest_listbox.curselection()[0]
            if cur == 0:
                self._suggest_listbox.selection_clear(0, tk.END)
                if self._search_entry:
                    self._search_entry.focus_set()
                return "break"
        return None

    def _on_suggest_click(self, event: Any):
        if not (self._suggest_listbox and self._suggest_items):
            return
        sel = self._suggest_listbox.curselection()
        if sel:
            idx = int(sel[0])
            if 0 <= idx < len(self._suggest_items):
                _disp, q_target = self._suggest_items[idx]
                self._select_suggested_query(q_target)

    def _on_suggest_enter(self, event: Any):
        self._on_suggest_click(event)

    def _select_suggested_query(self, query: str):
        if self._search_entry:
            self._search_entry.delete(0, tk.END)
            self._search_entry.insert(0, query)
        self._hide_suggestions()
        self._on_search()

    def _on_search_focus_in(self, event: Any):
        if not self._search_entry:
            return
        q = self._search_entry.get().strip().lstrip("🌍📍 ").strip()
        if q and not q.lower().startswith("auto"):
            self._on_search_key_release(event)

    def _on_search(self):
        self._hide_suggestions()
        if not self._search_entry:
            return
        query = self._search_entry.get().strip()
        query = query.lstrip("🌍📍 ").strip()
        q_lower = query.lower()
        if not query or "auto" in q_lower or "gps" in q_lower or "my location" in q_lower or "current location" in q_lower:
            target = "auto"
        else:
            target = query

        data = self.get_data()
        data["weather_city"] = target
        self.save_data(data)
        self._fetch_weather(city_override=target)

    def _on_auto_location(self):
        data = self.get_data()
        data["weather_city"] = "auto"
        self.save_data(data)
        if self._search_entry:
            self._search_entry.delete(0, tk.END)
            self._search_entry.insert(0, "Auto (GPS/IP)")
        self._fetch_weather(city_override="auto")

    def _set_unit(self, new_unit: str):
        data = self.get_data()
        if data.get("weather_unit") == new_unit:
            return
        data["weather_unit"] = new_unit
        self.save_data(data)
        self._update_unit_buttons(new_unit)
        self._fetch_weather()
        # Clear world weather cache so badges re-fetch in new unit
        self._world_weather_cache.clear()
        if self._active_tab == "world_clock":
            self._render_world_clock_tab()

    def _update_unit_buttons(self, unit: str):
        t = themes.get()
        acc = t.get("accent", "#e74c3c")
        btn_bg = t.get("btn", "#2c2e3f")
        fg_white = t.get("fg_white", "#ffffff")
        fg_dim = t.get("fg_dim", "#888888")

        if self._btn_c and self._btn_c.winfo_exists():
            if unit == "celsius":
                self._btn_c.configure(bg=acc, fg=fg_white)
            else:
                self._btn_c.configure(bg=btn_bg, fg=fg_dim)

        if self._btn_f and self._btn_f.winfo_exists():
            if unit == "fahrenheit":
                self._btn_f.configure(bg=acc, fg=fg_white)
            else:
                self._btn_f.configure(bg=btn_bg, fg=fg_dim)

    def _render_weather_data(self, data: dict[str, Any]):
        t = themes.get()
        fg_dim = t.get("fg_dim", "#888888")

        # 1. Update 3-Day Cards labels with fresh data
        forecast = data.get("forecast", [])
        for idx, card in enumerate(self._forecast_card_widgets):
            if idx < len(forecast):
                f_item = forecast[idx]
                card["day"].configure(text=f_item.get("label", ""))
                card["sub_day"].configure(text=f_item.get("sub_label", ""))
                card["icon"].configure(text=f_item.get("icon", "🌤️"))
                card["temp"].configure(text=f"{f_item.get('max')}° / {f_item.get('min')}°")
                card["rain"].configure(text=f"💧 {f_item.get('rain_prob', 0)}%")

        # 2. Update status label
        if self._status_lbl and self._status_lbl.winfo_exists():
            up_time = data.get("updated_time", "")
            self._status_lbl.configure(text=f"Updated at {up_time} • Live", fg=fg_dim)

        # 3. Update the selected day view (Today, Tomorrow, or Day 3)
        self._update_selected_day_view()

        # 4. Canvas configuration
        if self._canvas and self._canvas.winfo_exists():
            self._canvas.after(30, lambda: self._canvas.configure(scrollregion=self._canvas.bbox("all")) if self._canvas and self._canvas.winfo_exists() else None)

    def _select_day(self, day_idx: int):
        self._selected_day_idx = max(0, min(2, day_idx))
        self._selected_hour_idx = None
        self._update_selected_day_view()

    def _on_day_card_hover(self, day_i: int, is_enter: bool):
        if day_i == self._selected_day_idx:
            return
        if day_i < len(self._forecast_card_widgets):
            rec = self._forecast_card_widgets[day_i]
            box = rec.get("box")
            if box and box.winfo_exists():
                t = themes.get()
                bg_col = t.get("bg_hover", "#2c2e3f") if is_enter else t.get("bg_grid", "#181924")
                box.configure(bg=bg_col)

    def _update_selected_day_view(self):
        if not self.cached_weather:
            return
        data = self.cached_weather
        t = themes.get()
        acc = t.get("accent", "#e74c3c")
        bg_grid = t.get("bg_grid", "#181924")
        bg_hover = t.get("bg_hover", "#2c2e3f")
        fg_white = t.get("fg_white", "#ffffff")
        fg_dim = t.get("fg_dim", "#888888")

        forecast = data.get("forecast", [])
        if not forecast:
            return
        day_idx = min(self._selected_day_idx, len(forecast) - 1)
        cur_day = forecast[day_idx]
        unit = data.get("unit", "°C")
        wind_unit = data.get("wind_unit", "km/h")
        precip_unit = data.get("precip_unit", "mm")
        city_name = data.get("city", "Unknown City")
        country = data.get("country", "")

        # 1. Update 3-Day Cards Selection Highlights
        for idx, card in enumerate(self._forecast_card_widgets):
            f_box = card.get("box")
            active_lbl = card.get("active_lbl")
            d_lbl = card.get("day")
            if not (f_box and f_box.winfo_exists()):
                continue
            if idx == day_idx:
                f_box.configure(bg=bg_hover, highlightbackground=acc, highlightcolor=acc, highlightthickness=2)
                if active_lbl and active_lbl.winfo_exists():
                    active_lbl.configure(text="● VIEWING", bg=acc, fg=fg_white)
                if d_lbl and d_lbl.winfo_exists():
                    d_lbl.configure(fg=acc)
            else:
                f_box.configure(bg=bg_grid, highlightbackground=bg_grid, highlightcolor=bg_grid, highlightthickness=2)
                if active_lbl and active_lbl.winfo_exists():
                    active_lbl.configure(text="Click to view", bg=bg_grid, fg=fg_dim)
                if d_lbl and d_lbl.winfo_exists():
                    d_lbl.configure(fg=fg_dim)

        # 2. Update Hero Card & Metrics
        if day_idx == 0:
            # Today: Live Current Conditions
            loc_str = f"📍 {city_name}, {country}" if country else f"📍 {city_name}"
            if self._location_lbl and self._location_lbl.winfo_exists():
                self._location_lbl.configure(text=loc_str)

            tz = timezone(timedelta(seconds=self._current_utc_offset))
            now = datetime.now(tz)
            if self._live_clock_lbl and self._live_clock_lbl.winfo_exists():
                self._live_clock_lbl.configure(text=f"⏰ {now.strftime('%I:%M:%S %p')} • {now.strftime('%a, %d %b %Y')} ({self._current_tz_abbrev})", fg=acc)

            if self._hero_icon_lbl and self._hero_icon_lbl.winfo_exists():
                self._hero_icon_lbl.configure(text=data.get("icon", "🌤️"))

            temp_str = f"{data.get('temp', '--')}{unit}"
            if self._hero_temp_lbl and self._hero_temp_lbl.winfo_exists():
                self._hero_temp_lbl.configure(text=temp_str)

            if self._hero_desc_lbl and self._hero_desc_lbl.winfo_exists():
                self._hero_desc_lbl.configure(text=data.get("desc", ""))

            feels_str = f"Feels like {data.get('feels_like', '--')}{unit} • High {cur_day.get('max')}° / Low {cur_day.get('min')}°"
            if self._hero_feels_lbl and self._hero_feels_lbl.winfo_exists():
                self._hero_feels_lbl.configure(text=feels_str)

            if self._metric_humid_val and self._metric_humid_val.winfo_exists():
                self._metric_humid_val.configure(text=f"{data.get('humidity', 0)}%")
            if self._metric_wind_val and self._metric_wind_val.winfo_exists():
                self._metric_wind_val.configure(text=f"{data.get('wind', 0)} {wind_unit}")
            if self._metric_precip_val and self._metric_precip_val.winfo_exists():
                self._metric_precip_val.configure(text=f"{data.get('precip', 0)} {precip_unit} (💧 {cur_day.get('rain_prob', 0)}%)")
            if self._metric_range_val and self._metric_range_val.winfo_exists():
                self._metric_range_val.configure(text=f"{cur_day.get('max')}° / {cur_day.get('min')}°")

            advice_text = data.get("advice", "Have a wonderful day! ✨")
        else:
            # Tomorrow or Day 3 Forecast
            lbl_name = cur_day.get("label", "Forecast")
            sub_lbl = cur_day.get("sub_label", "")
            loc_str = f"📍 {city_name} • {lbl_name}'s Forecast"
            if self._location_lbl and self._location_lbl.winfo_exists():
                self._location_lbl.configure(text=loc_str)

            if self._live_clock_lbl and self._live_clock_lbl.winfo_exists():
                self._live_clock_lbl.configure(text=f"📅 {lbl_name} • {sub_lbl} ({cur_day.get('desc', '')})", fg=acc)

            if self._hero_icon_lbl and self._hero_icon_lbl.winfo_exists():
                self._hero_icon_lbl.configure(text=cur_day.get("icon", "🌤️"))

            temp_str = f"{cur_day.get('max')}° / {cur_day.get('min')}°"
            if self._hero_temp_lbl and self._hero_temp_lbl.winfo_exists():
                self._hero_temp_lbl.configure(text=temp_str)

            if self._hero_desc_lbl and self._hero_desc_lbl.winfo_exists():
                self._hero_desc_lbl.configure(text=f"{cur_day.get('desc', '')} Expected")

            feels_str = f"Expected High {cur_day.get('max')}° • Low {cur_day.get('min')}° • 💧 {cur_day.get('rain_prob', 0)}% Rain Chance"
            if self._hero_feels_lbl and self._hero_feels_lbl.winfo_exists():
                self._hero_feels_lbl.configure(text=feels_str)

            day_hours = cur_day.get("hourly", [])
            avg_hum = int(sum(h.get("humidity", 0) for h in day_hours) / max(1, len(day_hours))) if day_hours else 0
            max_w = round(max((h.get("wind", 0.0) for h in day_hours), default=0.0), 1)
            tot_p = round(sum(h.get("precip", 0.0) for h in day_hours), 1)

            if self._metric_humid_val and self._metric_humid_val.winfo_exists():
                self._metric_humid_val.configure(text=f"{avg_hum}% (Avg)")
            if self._metric_wind_val and self._metric_wind_val.winfo_exists():
                self._metric_wind_val.configure(text=f"{max_w} {wind_unit} (Max)")
            if self._metric_precip_val and self._metric_precip_val.winfo_exists():
                self._metric_precip_val.configure(text=f"{tot_p} {precip_unit} (💧 {cur_day.get('rain_prob', 0)}%)")
            if self._metric_range_val and self._metric_range_val.winfo_exists():
                self._metric_range_val.configure(text=f"{cur_day.get('max')}° / {cur_day.get('min')}°")

            advice_text = cur_day.get("advice", "Have a wonderful day! ✨")

        if self._pet_advice_lbl and self._pet_advice_lbl.winfo_exists():
            self._pet_advice_lbl.configure(text=f'"{advice_text}"')

        if self._say_btn and self._say_btn.winfo_exists():
            if day_idx == 0:
                self._say_btn.configure(text="💬 Say Live Weather & Time")
            else:
                self._say_btn.configure(text=f"💬 Say {cur_day.get('label', 'Day')}'s Weather")

        # 3. Update Hourly Forecast Header & Render Cards
        if self._hourly_title_lbl and self._hourly_title_lbl.winfo_exists():
            self._hourly_title_lbl.configure(text=f"🕒 HOURLY FORECAST • {cur_day.get('label', '').upper()} ({cur_day.get('sub_label', '')})")

        self._render_hourly_cards(cur_day.get("hourly", []), day_idx)

    def _render_hourly_cards(self, day_hours: list[dict[str, Any]], day_idx: int):
        if not (self._hourly_frame and self._hourly_canvas and self._hourly_frame.winfo_exists()):
            return
        t = themes.get()
        acc = t.get("accent", "#e74c3c")
        bg_grid = t.get("bg_grid", "#181924")
        bg_hover = t.get("bg_hover", "#2c2e3f")
        fg_main = t.get("fg_main", "#ffffff")
        fg_dim = t.get("fg_dim", "#888888")

        for child in self._hourly_frame.winfo_children():
            child.destroy()
        self._hourly_card_widgets = []

        tz = timezone(timedelta(seconds=self._current_utc_offset))
        now_dt = datetime.now(tz)
        current_hour = now_dt.hour

        target_scroll_idx = 0
        if day_idx == 0:
            target_scroll_idx = current_hour

        for h_idx, h_item in enumerate(day_hours):
            h_val = h_item.get("hour", h_idx)
            is_now = (day_idx == 0 and h_val == current_hour)

            c_bg = bg_hover if is_now else bg_grid
            hl_col = acc if is_now else bg_grid
            hl_th = 2 if is_now else 1

            h_box = tk.Frame(
                self._hourly_frame,
                bg=c_bg,
                padx=6,
                pady=5,
                highlightbackground=hl_col,
                highlightcolor=hl_col,
                highlightthickness=hl_th,
                cursor="hand2",
            )
            h_box.pack(side="left", padx=2, pady=2)

            if is_now:
                t_lbl = tk.Label(h_box, text="NOW", bg=c_bg, fg=acc, font=("Segoe UI", 8, "bold"), cursor="hand2")
            else:
                t_lbl = tk.Label(h_box, text=h_item.get("label_12", f"{h_val}:00"), bg=c_bg, fg=fg_main, font=("Segoe UI", 7, "bold"), cursor="hand2")
            t_lbl.pack()

            sub_lbl = tk.Label(h_box, text=h_item.get("label_24", ""), bg=c_bg, fg=fg_dim, font=("Segoe UI", 6), cursor="hand2")
            sub_lbl.pack()

            i_lbl = tk.Label(h_box, text=h_item.get("icon", "🌤️"), bg=c_bg, font=("Segoe UI Emoji", 14), cursor="hand2")
            i_lbl.pack(pady=1)

            temp_val = h_item.get("temp", 0.0)
            deg_lbl = tk.Label(h_box, text=f"{round(temp_val)}°", bg=c_bg, fg=fg_main, font=("Segoe UI", 8, "bold"), cursor="hand2")
            deg_lbl.pack()

            rain_p = h_item.get("rain_prob", 0)
            if rain_p > 0:
                r_col = "#5dade2" if "#5dade2" != fg_main else acc
                r_lbl = tk.Label(h_box, text=f"💧{rain_p}%", bg=c_bg, fg=r_col, font=("Segoe UI", 7, "bold"), cursor="hand2")
            else:
                r_lbl = tk.Label(h_box, text="💧0%", bg=c_bg, fg=fg_dim, font=("Segoe UI", 6), cursor="hand2")
            r_lbl.pack()

            record = {
                "box": h_box,
                "hour_item": h_item,
                "is_now": is_now,
                "labels": [t_lbl, sub_lbl, i_lbl, deg_lbl, r_lbl],
            }
            self._hourly_card_widgets.append(record)

            def _bind_all(w, item=h_item, idx=h_idx):
                w.bind("<Button-1>", lambda e: self._select_hour(idx, item))
                w.bind("<Enter>", lambda e: self._on_hour_hover(idx, item))
                w.bind("<Leave>", lambda e: self._on_hour_leave(idx))
                w.bind("<MouseWheel>", self._on_hourly_mousewheel)

            for widget in [h_box, t_lbl, sub_lbl, i_lbl, deg_lbl, r_lbl]:
                _bind_all(widget)

        if self._hour_inspector_lbl and self._hour_inspector_lbl.winfo_exists():
            day_name = "Today" if day_idx == 0 else ("Tomorrow" if day_idx == 1 else "Day 3")
            self._hour_inspector_lbl.configure(
                text=f"💡 Showing 24 hours of {day_name} • Click any hour card above to inspect conditions!",
                fg=fg_dim
            )

        def _apply_scroll():
            if not (self._hourly_canvas and self._hourly_canvas.winfo_exists()):
                return
            self._hourly_canvas.configure(scrollregion=self._hourly_canvas.bbox("all"))
            if target_scroll_idx > 0 and len(day_hours) > 0:
                frac = max(0.0, min(1.0, (target_scroll_idx - 1) / float(len(day_hours))))
                self._hourly_canvas.xview_moveto(frac)
            else:
                self._hourly_canvas.xview_moveto(0.0)

        self.root.after(40, _apply_scroll)

    def _select_hour(self, h_idx: int, h_item: dict[str, Any]):
        self._selected_hour_idx = h_idx
        t = themes.get()
        acc = t.get("accent", "#e74c3c")
        bg_hover = t.get("bg_hover", "#2c2e3f")
        bg_grid = t.get("bg_grid", "#181924")
        fg_main = t.get("fg_main", "#ffffff")

        for idx, rec in enumerate(self._hourly_card_widgets):
            box = rec.get("box")
            if not (box and box.winfo_exists()):
                continue
            if idx == h_idx:
                box.configure(bg=bg_hover, highlightbackground=acc, highlightcolor=acc, highlightthickness=2)
            elif rec.get("is_now"):
                box.configure(bg=bg_hover, highlightbackground=acc, highlightcolor=acc, highlightthickness=1)
            else:
                box.configure(bg=bg_grid, highlightbackground=bg_grid, highlightcolor=bg_grid, highlightthickness=1)

        if self._hour_inspector_lbl and self._hour_inspector_lbl.winfo_exists():
            data = self.cached_weather or {}
            unit = data.get("unit", "°C")
            precip_unit = data.get("precip_unit", "mm")
            wind_unit = data.get("wind_unit", "km/h")
            rain_p = h_item.get("rain_prob", 0)
            precip = h_item.get("precip", 0.0)
            msg = (
                f"🕒 {h_item.get('label_12')} ({h_item.get('label_24')}) • {h_item.get('desc')} {h_item.get('icon')} • "
                f"Temp: {h_item.get('temp')}{unit} (Feels {h_item.get('feels_like')}{unit}) • "
                f"Rain: 💧{rain_p}% ({precip} {precip_unit}) • "
                f"Wind: 💨 {h_item.get('wind')} {wind_unit} • Humidity: 💧 {h_item.get('humidity')}%"
            )
            self._hour_inspector_lbl.configure(text=msg, fg=fg_main)

    def _on_hour_hover(self, h_idx: int, h_item: dict[str, Any]):
        if self._selected_hour_idx is not None:
            return
        if self._hour_inspector_lbl and self._hour_inspector_lbl.winfo_exists():
            data = self.cached_weather or {}
            unit = data.get("unit", "°C")
            rain_p = h_item.get("rain_prob", 0)
            msg = (
                f"🕒 {h_item.get('label_12')} ({h_item.get('label_24')}) • {h_item.get('desc')} {h_item.get('icon')} • "
                f"Temp: {h_item.get('temp')}{unit} (Feels {h_item.get('feels_like')}{unit}) • "
                f"Rain: 💧{rain_p}% • Wind: 💨 {h_item.get('wind')} {data.get('wind_unit', 'km/h')}"
            )
            self._hour_inspector_lbl.configure(text=msg, fg=themes.get().get("fg_main", "#ffffff"))

    def _on_hour_leave(self, h_idx: int):
        if self._selected_hour_idx is not None:
            return
        if self._hour_inspector_lbl and self._hour_inspector_lbl.winfo_exists():
            fg_dim = themes.get().get("fg_dim", "#888888")
            day_name = "Today" if self._selected_day_idx == 0 else ("Tomorrow" if self._selected_day_idx == 1 else "Day 3")
            self._hour_inspector_lbl.configure(
                text=f"💡 Showing 24 hours of {day_name} • Click any hour card above to inspect conditions!",
                fg=fg_dim
            )

    def _scroll_hourly(self, steps: int):
        if self._hourly_canvas and self._hourly_canvas.winfo_exists():
            self._hourly_canvas.xview_scroll(steps, "units")

    def _jump_hourly(self, hour_target: int):
        if self._hourly_canvas and self._hourly_canvas.winfo_exists():
            frac = max(0.0, min(1.0, hour_target / 24.0))
            self._hourly_canvas.xview_moveto(frac)

    def _jump_to_now(self):
        if self._selected_day_idx != 0:
            self._select_day(0)
        else:
            tz = timezone(timedelta(seconds=self._current_utc_offset))
            curr_h = datetime.now(tz).hour
            self._jump_hourly(curr_h)

    def _on_hourly_mousewheel(self, event):
        if self._hourly_canvas and self._hourly_canvas.winfo_exists():
            delta = getattr(event, "delta", 0)
            if delta:
                self._hourly_canvas.xview_scroll(int(-1 * (delta / 120)), "units")
        return "break"

    # ── Country Picker Dialog (200+ Countries) ───────────────────────────────
    def _open_country_picker(self, for_world_clock: bool = False):
        if not (self.win and self.win.winfo_exists()):
            return
        t = themes.get()
        bg = t.get("bg_card", "#20222e")
        bg_grid = t.get("bg_grid", "#181924")
        fg = t.get("fg_main", "#ffffff")
        dim = t.get("fg_dim", "#888888")
        acc = t.get("accent", "#e74c3c")
        btn_bg = t.get("btn", "#2c2e3f")
        border = t.get("border", "#181920")

        dialog = tk.Toplevel(self.win)
        dialog.title("🌍 Choose Country" if not for_world_clock else "➕ Add World Clock")
        dialog.geometry(f"330x460+{self.win.winfo_x()+15}+{self.win.winfo_y()+35}")
        dialog.attributes("-topmost", True)
        dialog.configure(bg=border)
        dialog.resizable(False, False)
        dialog.grab_set()

        outer_d = tk.Frame(dialog, bg=bg, padx=10, pady=10)
        outer_d.pack(fill="both", expand=True, padx=2, pady=2)

        hdr_d = tk.Frame(outer_d, bg=bg)
        hdr_d.pack(fill="x", pady=(0, 6))
        tk.Label(
            hdr_d,
            text="🌍 BROWSE COUNTRIES (200+)",
            bg=bg,
            fg=acc,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")
        close_lbl = tk.Label(
            hdr_d,
            text="✕",
            bg=bg,
            fg=fg,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            padx=4
        )
        close_lbl.pack(side="right")
        close_lbl.bind("<Button-1>", lambda e: dialog.destroy())

        tk.Label(
            outer_d,
            text="Type to search any country or capital:",
            bg=bg,
            fg=dim,
            font=("Segoe UI", 8),
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        filter_var = tk.StringVar()
        filter_entry = tk.Entry(
            outer_d,
            textvariable=filter_var,
            font=("Segoe UI", 9),
            bg=bg_grid,
            fg=fg,
            insertbackground=fg,
            relief="flat",
            bd=0
        )
        filter_entry.pack(fill="x", ipady=4, padx=1, pady=(0, 6))
        filter_entry.focus_set()

        lb_frame = tk.Frame(outer_d, bg=bg)
        lb_frame.pack(fill="both", expand=True)

        lb = tk.Listbox(
            lb_frame,
            font=("Segoe UI", 8),
            relief="flat",
            bd=0,
            selectmode="single",
            bg=bg_grid,
            fg=fg,
            selectbackground=acc,
            selectforeground="#ffffff",
            activestyle="none",
            highlightthickness=0,
        )
        sb = tk.Scrollbar(lb_frame, command=lb.yview)
        lb.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        lb.pack(side="left", fill="both", expand=True)

        def _populate(filter_str: str = ""):
            lb.delete(0, tk.END)
            query = filter_str.strip().lower()
            for row in ALL_TIMEZONES:
                label = row[0]
                if not query or query in label.lower():
                    lb.insert(tk.END, label)

        _populate()
        filter_var.trace_add("write", lambda *_: _populate(filter_var.get()))

        def _select():
            sel = lb.curselection()
            if not sel:
                return
            chosen_label = str(lb.get(sel[0]))
            dialog.destroy()

            data = self.get_data()
            if for_world_clock:
                cities = list(data.get("world_clock_cities", list(DEFAULT_CITIES)))
                if chosen_label not in cities:
                    cities.append(chosen_label)
                data["world_clock_cities"] = cities
                self.save_data(data)
                self._render_world_clock_tab()
            else:
                data["weather_city"] = chosen_label
                self.save_data(data)
                if self._search_entry:
                    self._search_entry.delete(0, tk.END)
                    self._search_entry.insert(0, chosen_label)
                self._fetch_weather(city_override=chosen_label)

        lb.bind("<Double-Button-1>", lambda e: _select())
        filter_entry.bind("<Return>", lambda e: _select())

        btn_row = tk.Frame(outer_d, bg=bg)
        btn_row.pack(fill="x", pady=(8, 0))

        tk.Button(
            btn_row,
            text="Cancel",
            bg=btn_bg,
            fg=fg,
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=10,
            pady=4,
            command=dialog.destroy,
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        tk.Button(
            btn_row,
            text="Add to Clocks" if for_world_clock else "Get Weather",
            bg=acc,
            fg="#ffffff",
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=10,
            pady=4,
            command=_select,
        ).pack(side="right", expand=True, fill="x", padx=(4, 0))

    # ── UI Construction ──────────────────────────────────────────────────────
    def _build(self, x: int, y: int):
        t = themes.get()
        bg_card = t.get("bg_card", "#20222e")
        acc = t.get("accent", "#e74c3c")
        border = t.get("border", "#181920")
        fg_main = t.get("fg_main", "#ffffff")

        self.win = tk.Toplevel(self.root)
        self.win.title("🌤️ Weather & World Time")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        target_w, target_h = 390, 620
        safe_x = max(10, min(x, sw - target_w - 15))
        safe_y = max(10, min(y, sh - target_h - 45))

        self.win.geometry(f"{target_w}x{target_h}+{safe_x}+{safe_y}")
        self.win.minsize(360, 520)
        self.win.attributes("-topmost", True)
        self.win.configure(bg=border)
        self.win.resizable(True, True)
        self.win.protocol("WM_DELETE_WINDOW", self.hide)

        outer = tk.Frame(self.win, bg=bg_card, padx=8, pady=8)
        outer.pack(fill="both", expand=True, padx=2, pady=2)

        # ── Header ──
        hdr = tk.Frame(outer, bg=bg_card)
        hdr.pack(fill="x", pady=(0, 4))
        hdr.bind("<ButtonPress-1>", self._drag_start)
        hdr.bind("<B1-Motion>", self._drag_move)

        title_lbl = tk.Label(
            hdr,
            text="🌤️ WEATHER & WORLD TIME",
            bg=bg_card,
            fg=acc,
            font=("Segoe UI", 9, "bold"),
            cursor="fleur",
        )
        title_lbl.pack(side="left")
        title_lbl.bind("<ButtonPress-1>", self._drag_start)
        title_lbl.bind("<B1-Motion>", self._drag_move)

        close_btn = tk.Label(
            hdr,
            text="✕",
            bg=bg_card,
            fg=fg_main,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            padx=4,
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.hide())

        if self.on_menu:
            on_menu_fn = self.on_menu
            mb = tk.Label(
                hdr,
                text="☰",
                bg=bg_card,
                fg=fg_main,
                font=("Segoe UI", 9, "bold"),
                cursor="hand2",
                padx=4,
            )
            mb.pack(side="right", padx=(0, 4))
            mb.bind("<Button-1>", lambda e: on_menu_fn(close_win=self.win, hide_fn=self.hide))

        refresh_btn = tk.Label(
            hdr,
            text="🔄",
            bg=bg_card,
            fg=fg_main,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            padx=4,
        )
        refresh_btn.pack(side="right", padx=(0, 4))
        refresh_btn.bind("<Button-1>", lambda e: self._on_manual_refresh())

        # ── Tab Navigation Bar ──
        tab_nav = tk.Frame(outer, bg=bg_card)
        tab_nav.pack(fill="x", pady=(2, 6))

        self._btn_tab_weather = tk.Button(
            tab_nav,
            text="🌤️ Live Weather & Clock",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            bd=0,
            pady=3,
            cursor="hand2",
            command=lambda: self._switch_tab("weather"),
        )
        self._btn_tab_weather.pack(side="left", expand=True, fill="x", padx=(0, 2))

        self._btn_tab_clock = tk.Button(
            tab_nav,
            text="🌐 World Clocks & Weather",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            bd=0,
            pady=3,
            cursor="hand2",
            command=lambda: self._switch_tab("world_clock"),
        )
        self._btn_tab_clock.pack(side="left", expand=True, fill="x", padx=(2, 0))

        # ── Body Container (Swapped on Tab Change) ──
        self._body_container = tk.Frame(outer, bg=bg_card)
        self._body_container.pack(fill="both", expand=True)

        self._switch_tab(self._active_tab)

    def _on_manual_refresh(self):
        if self._active_tab == "weather":
            self._fetch_weather()
        else:
            self._world_weather_cache.clear()
            self._render_world_clock_tab()

    def _switch_tab(self, tab_name: str):
        self._active_tab = tab_name
        self._update_tab_buttons()

        if not self._body_container or not self._body_container.winfo_exists():
            return

        for child in self._body_container.winfo_children():
            child.destroy()

        if tab_name == "weather":
            self._render_weather_tab()
        else:
            self._render_world_clock_tab()

    def _update_tab_buttons(self):
        t = themes.get()
        acc = t.get("accent", "#e74c3c")
        btn_bg = t.get("btn", "#2c2e3f")
        fg_white = t.get("fg_white", "#ffffff")
        fg_dim = t.get("fg_dim", "#888888")

        if self._btn_tab_weather and self._btn_tab_weather.winfo_exists():
            if self._active_tab == "weather":
                self._btn_tab_weather.configure(bg=acc, fg=fg_white)
            else:
                self._btn_tab_weather.configure(bg=btn_bg, fg=fg_dim)

        if self._btn_tab_clock and self._btn_tab_clock.winfo_exists():
            if self._active_tab == "world_clock":
                self._btn_tab_clock.configure(bg=acc, fg=fg_white)
            else:
                self._btn_tab_clock.configure(bg=btn_bg, fg=fg_dim)

    # ── Tab 1: Live Weather & Clock ──────────────────────────────────────────
    def _render_weather_tab(self):
        if not self._body_container:
            return
        t = themes.get()
        bg_card = t.get("bg_card", "#20222e")
        bg_grid = t.get("bg_grid", "#181924")
        acc = t.get("accent", "#e74c3c")
        btn_bg = t.get("btn", "#2c2e3f")
        fg_main = t.get("fg_main", "#ffffff")
        fg_dim = t.get("fg_dim", "#888888")
        fg_white = t.get("fg_white", "#ffffff")

        # Search Toolbar
        toolbar = tk.Frame(self._body_container, bg=bg_card)
        toolbar.pack(fill="x", pady=(0, 6))
        self._toolbar_frame = toolbar

        saved_data = self.get_data()
        cur_city = saved_data.get("weather_city", "auto")
        cur_unit = saved_data.get("weather_unit", "celsius")

        self._search_entry = tk.Entry(
            toolbar,
            bg=bg_grid,
            fg=fg_main,
            insertbackground=fg_main,
            relief="flat",
            bd=0,
            font=("Segoe UI", 9),
        )
        self._search_entry.pack(side="left", fill="x", expand=True, ipady=3, padx=(0, 4))
        self._search_entry.insert(0, "Auto (GPS/IP)" if cur_city == "auto" else cur_city)
        self._search_entry.bind("<Return>", lambda e: self._on_search())
        self._search_entry.bind("<KeyRelease>", self._on_search_key_release)
        self._search_entry.bind("<Down>", self._on_search_down_arrow)
        self._search_entry.bind("<Escape>", lambda e: self._hide_suggestions())
        self._search_entry.bind("<FocusIn>", self._on_search_focus_in)

        btn_search = tk.Button(
            toolbar,
            text="🔍",
            bg=btn_bg,
            fg=fg_main,
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=6,
            pady=2,
            command=self._on_search,
        )
        btn_search.pack(side="left", padx=(0, 3))

        btn_auto = tk.Button(
            toolbar,
            text="📍",
            bg=btn_bg,
            fg=fg_main,
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=6,
            pady=2,
            command=self._on_auto_location,
        )
        btn_auto.pack(side="left", padx=(0, 3))

        btn_countries = tk.Button(
            toolbar,
            text="🌍",
            bg=btn_bg,
            fg=fg_main,
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=6,
            pady=2,
            command=lambda: self._open_country_picker(for_world_clock=False),
        )
        btn_countries.pack(side="left", padx=(0, 5))

        self._btn_c = tk.Button(
            toolbar,
            text="°C",
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=4,
            pady=2,
            command=lambda: self._set_unit("celsius"),
        )
        self._btn_c.pack(side="left", padx=(0, 2))

        self._btn_f = tk.Button(
            toolbar,
            text="°F",
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=4,
            pady=2,
            command=lambda: self._set_unit("fahrenheit"),
        )
        self._btn_f.pack(side="left")
        self._update_unit_buttons(cur_unit)

        # Scrollable Body Area
        scroll_container = tk.Frame(self._body_container, bg=bg_card)
        scroll_container.pack(fill="both", expand=True, pady=(2, 0))

        self._canvas = tk.Canvas(scroll_container, bg=bg_card, highlightthickness=0)
        self._sb = tk.Scrollbar(scroll_container, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._sb.set)

        self._sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self._canvas.bind("<Button-1>", lambda e: self._hide_suggestions())

        # Autocomplete Suggestions Floating Dropdown
        border = t.get("border", "#181920")
        self._suggest_frame = tk.Frame(self._body_container, bg=border, padx=1, pady=1)
        s_inner = tk.Frame(self._suggest_frame, bg=bg_card)
        s_inner.pack(fill="both", expand=True)

        s_hdr = tk.Frame(s_inner, bg=bg_grid, padx=6, pady=3)
        s_hdr.pack(fill="x")
        tk.Label(
            s_hdr,
            text="💡 MATCHING COUNTRIES & CITIES",
            bg=bg_grid,
            fg=acc,
            font=("Segoe UI", 7, "bold"),
            anchor="w",
        ).pack(side="left")

        s_box_frame = tk.Frame(s_inner, bg=bg_card)
        s_box_frame.pack(fill="both", expand=True)

        self._suggest_listbox = tk.Listbox(
            s_box_frame,
            bg=bg_card,
            fg=fg_main,
            selectbackground=acc,
            selectforeground=fg_white,
            font=("Segoe UI", 9),
            relief="flat",
            bd=0,
            highlightthickness=0,
            activestyle="none",
            exportselection=False,
        )
        s_sb = tk.Scrollbar(s_box_frame, orient="vertical", command=self._suggest_listbox.yview)
        self._suggest_listbox.configure(yscrollcommand=s_sb.set)

        s_sb.pack(side="right", fill="y")
        self._suggest_listbox.pack(side="left", fill="both", expand=True)

        self._suggest_listbox.bind("<ButtonRelease-1>", self._on_suggest_click)
        self._suggest_listbox.bind("<Return>", self._on_suggest_enter)
        self._suggest_listbox.bind("<Escape>", lambda e: self._hide_suggestions())
        self._suggest_listbox.bind("<Up>", self._on_suggest_up_arrow)

        content = tk.Frame(self._canvas, bg=bg_card)
        self._content_id = self._canvas.create_window((0, 0), window=content, anchor="nw")

        def _on_content_config(e: Any):
            if self._canvas and self._canvas.winfo_exists():
                self._canvas.configure(scrollregion=self._canvas.bbox("all"))

        def _on_canvas_config(e: Any):
            if self._canvas and self._canvas.winfo_exists() and self._content_id is not None:
                self._canvas.itemconfig(self._content_id, width=max(10, e.width))

        content.bind("<Configure>", _on_content_config)
        self._canvas.bind("<Configure>", _on_canvas_config)

        # Status Notice
        self._status_lbl = tk.Label(
            content,
            text="Connecting to satellite...",
            bg=bg_card,
            fg=fg_dim,
            font=("Segoe UI", 7),
        )
        self._status_lbl.pack(fill="x", pady=(0, 4))

        # Hero Card: Combined Live Clock / Selected Day Overview
        hero_card = tk.Frame(content, bg=bg_grid, padx=12, pady=10)
        hero_card.pack(fill="x", pady=(0, 8))

        self._location_lbl = tk.Label(
            hero_card,
            text="📍 Loading Location...",
            bg=bg_grid,
            fg=fg_main,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        self._location_lbl.pack(fill="x", pady=(0, 2))

        # Live Digital Ticking Clock / Selected Day Badge
        self._live_clock_lbl = tk.Label(
            hero_card,
            text="⏰ Loading local time...",
            bg=bg_grid,
            fg=acc,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        )
        self._live_clock_lbl.pack(fill="x", pady=(0, 4))

        hero_body = tk.Frame(hero_card, bg=bg_grid)
        hero_body.pack(fill="x", pady=2)

        self._hero_icon_lbl = tk.Label(
            hero_body,
            text="🌤️",
            bg=bg_grid,
            font=("Segoe UI Emoji", 34),
            padx=6,
        )
        self._hero_icon_lbl.pack(side="left")

        hero_right = tk.Frame(hero_body, bg=bg_grid)
        hero_right.pack(side="left", padx=(10, 0))

        self._hero_temp_lbl = tk.Label(
            hero_right,
            text="--°",
            bg=bg_grid,
            fg=fg_main,
            font=("Segoe UI", 26, "bold"),
            anchor="w",
        )
        self._hero_temp_lbl.pack(anchor="w")

        self._hero_desc_lbl = tk.Label(
            hero_right,
            text="Loading...",
            bg=bg_grid,
            fg=fg_main,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        )
        self._hero_desc_lbl.pack(anchor="w")

        self._hero_feels_lbl = tk.Label(
            hero_right,
            text="Feels like --°",
            bg=bg_grid,
            fg=fg_dim,
            font=("Segoe UI", 8),
            anchor="w",
        )
        self._hero_feels_lbl.pack(anchor="w")

        # 3-Day Forecast Section (Clickable Cards)
        fc_hdr = tk.Frame(content, bg=bg_card)
        fc_hdr.pack(fill="x", pady=(4, 2))

        tk.Label(
            fc_hdr,
            text="📅 3-DAY FORECAST (Click day to view hours)",
            bg=bg_card,
            fg=fg_dim,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).pack(side="left")

        fc_row = tk.Frame(content, bg=bg_card)
        fc_row.pack(fill="x", pady=(0, 6))

        self._forecast_card_widgets = []
        for i in range(3):
            f_box = tk.Frame(
                fc_row,
                bg=bg_grid,
                padx=4,
                pady=6,
                highlightbackground=bg_grid,
                highlightcolor=bg_grid,
                highlightthickness=2,
                cursor="hand2",
            )
            f_box.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 4, 0))

            d_lbl = tk.Label(f_box, text="---", bg=bg_grid, fg=fg_dim, font=("Segoe UI", 8, "bold"), cursor="hand2")
            d_lbl.pack()

            sub_d_lbl = tk.Label(f_box, text="---", bg=bg_grid, fg=fg_dim, font=("Segoe UI", 6), cursor="hand2")
            sub_d_lbl.pack()

            i_lbl = tk.Label(f_box, text="🌤️", bg=bg_grid, font=("Segoe UI Emoji", 16), cursor="hand2")
            i_lbl.pack(pady=1)

            t_lbl = tk.Label(f_box, text="--°/--°", bg=bg_grid, fg=fg_main, font=("Segoe UI", 8, "bold"), cursor="hand2")
            t_lbl.pack()

            r_lbl = tk.Label(f_box, text="💧 0%", bg=bg_grid, fg=fg_dim, font=("Segoe UI", 7), cursor="hand2")
            r_lbl.pack()

            act_lbl = tk.Label(f_box, text="Click to view", bg=bg_grid, fg=fg_dim, font=("Segoe UI", 6, "bold"), cursor="hand2")
            act_lbl.pack(pady=(2, 0))

            card_rec = {
                "box": f_box,
                "day": d_lbl,
                "sub_day": sub_d_lbl,
                "icon": i_lbl,
                "temp": t_lbl,
                "rain": r_lbl,
                "active_lbl": act_lbl,
            }
            self._forecast_card_widgets.append(card_rec)

            def _bind_card(w, day_i=i):
                w.bind("<Button-1>", lambda e: self._select_day(day_i))
                w.bind("<Enter>", lambda e: self._on_day_card_hover(day_i, True))
                w.bind("<Leave>", lambda e: self._on_day_card_hover(day_i, False))

            for widget in [f_box, d_lbl, sub_d_lbl, i_lbl, t_lbl, r_lbl, act_lbl]:
                _bind_card(widget)

        # Hourly Forecast Section ("by hour base")
        hourly_hdr = tk.Frame(content, bg=bg_card)
        hourly_hdr.pack(fill="x", pady=(6, 2))

        self._hourly_title_lbl = tk.Label(
            hourly_hdr,
            text="🕒 HOURLY FORECAST • TODAY",
            bg=bg_card,
            fg=fg_dim,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self._hourly_title_lbl.pack(side="left")

        # Hourly Navigation Arrows
        nav_f = tk.Frame(hourly_hdr, bg=bg_card)
        nav_f.pack(side="right")

        tk.Button(
            nav_f,
            text="◀ Earlier",
            bg=btn_bg,
            fg=fg_main,
            relief="flat",
            bd=0,
            font=("Segoe UI", 7, "bold"),
            cursor="hand2",
            padx=6,
            pady=1,
            command=lambda: self._scroll_hourly(-3),
        ).pack(side="left", padx=(0, 2))

        tk.Button(
            nav_f,
            text="Later ▶",
            bg=btn_bg,
            fg=fg_main,
            relief="flat",
            bd=0,
            font=("Segoe UI", 7, "bold"),
            cursor="hand2",
            padx=6,
            pady=1,
            command=lambda: self._scroll_hourly(3),
        ).pack(side="left")

        # Quick Time Jump Pills
        q_row = tk.Frame(content, bg=bg_card)
        q_row.pack(fill="x", pady=(0, 4))
        self._quick_jump_frame = q_row

        tk.Label(
            q_row,
            text="Jump:",
            bg=bg_card,
            fg=fg_dim,
            font=("Segoe UI", 7),
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            q_row,
            text="⚡ Now",
            bg=btn_bg,
            fg=acc,
            relief="flat",
            bd=0,
            font=("Segoe UI", 7, "bold"),
            cursor="hand2",
            padx=5,
            pady=1,
            command=lambda: self._jump_to_now(),
        ).pack(side="left", padx=(0, 3))

        for j_lbl, j_hr in [("🌅 6 AM", 6), ("☀️ 12 PM", 12), ("🌆 6 PM", 18), ("🌙 10 PM", 22)]:
            tk.Button(
                q_row,
                text=j_lbl,
                bg=btn_bg,
                fg=fg_main,
                relief="flat",
                bd=0,
                font=("Segoe UI", 7),
                cursor="hand2",
                padx=5,
                pady=1,
                command=lambda h=j_hr: self._jump_hourly(h),
            ).pack(side="left", padx=(0, 3))

        # Horizontal Scrollable Container for Hourly Cards
        h_scroll_container = tk.Frame(content, bg=bg_card)
        h_scroll_container.pack(fill="x", pady=(0, 2))

        self._hourly_canvas = tk.Canvas(
            h_scroll_container,
            bg=bg_card,
            height=106,
            highlightthickness=0
        )
        self._hourly_sb = tk.Scrollbar(
            h_scroll_container,
            orient="horizontal",
            command=self._hourly_canvas.xview
        )
        self._hourly_canvas.configure(xscrollcommand=self._hourly_sb.set)

        self._hourly_canvas.pack(fill="x", expand=True)
        self._hourly_sb.pack(fill="x")

        self._hourly_frame = tk.Frame(self._hourly_canvas, bg=bg_card)
        self._hourly_frame_id = self._hourly_canvas.create_window((0, 0), window=self._hourly_frame, anchor="nw")

        def _on_hf_config(e):
            if self._hourly_canvas and self._hourly_canvas.winfo_exists():
                self._hourly_canvas.configure(scrollregion=self._hourly_canvas.bbox("all"))

        self._hourly_frame.bind("<Configure>", _on_hf_config)
        self._hourly_canvas.bind("<MouseWheel>", self._on_hourly_mousewheel)
        self._hourly_frame.bind("<MouseWheel>", self._on_hourly_mousewheel)

        # Selected Hour Inspector / Condition Info Bar
        self._hour_inspector_lbl = tk.Label(
            content,
            text="💡 Showing 24 hours of Today • Click any hour card above to inspect conditions!",
            bg=bg_grid,
            fg=fg_dim,
            font=("Segoe UI", 7),
            padx=8,
            pady=4,
            anchor="w",
            wraplength=350,
            justify="left",
        )
        self._hour_inspector_lbl.pack(fill="x", pady=(2, 6))

        # Detail Metrics 2x2 Grid
        metrics_frame = tk.Frame(content, bg=bg_card)
        metrics_frame.pack(fill="x", pady=(0, 8))

        def make_metric_box(parent, title: str, init_val: str):
            box = tk.Frame(parent, bg=bg_grid, padx=8, pady=6)
            t_lbl = tk.Label(box, text=title, bg=bg_grid, fg=fg_dim, font=("Segoe UI", 7))
            t_lbl.pack(anchor="w")
            v_lbl = tk.Label(box, text=init_val, bg=bg_grid, fg=fg_main, font=("Segoe UI", 9, "bold"))
            v_lbl.pack(anchor="w")
            return box, v_lbl

        row1 = tk.Frame(metrics_frame, bg=bg_card)
        row1.pack(fill="x", pady=(0, 4))
        box1, self._metric_humid_val = make_metric_box(row1, "💧 Humidity", "--%")
        box1.pack(side="left", fill="x", expand=True, padx=(0, 4))
        box2, self._metric_wind_val = make_metric_box(row1, "💨 Wind", "-- km/h")
        box2.pack(side="left", fill="x", expand=True)

        row2 = tk.Frame(metrics_frame, bg=bg_card)
        row2.pack(fill="x")
        box3, self._metric_precip_val = make_metric_box(row2, "🌧️ Precipitation", "-- mm")
        box3.pack(side="left", fill="x", expand=True, padx=(0, 4))
        box4, self._metric_range_val = make_metric_box(row2, "🌡️ High / Low", "--° / --°")
        box4.pack(side="left", fill="x", expand=True)

        # Pet Companion Advice Box
        pet_box = tk.Frame(content, bg=bg_grid, padx=10, pady=8)
        pet_box.pack(fill="x", pady=(0, 6))

        pet_hdr = tk.Frame(pet_box, bg=bg_grid)
        pet_hdr.pack(fill="x")
        tk.Label(
            pet_hdr,
            text="🐾 Companion Weather & Time Advice",
            bg=bg_grid,
            fg=acc,
            font=("Segoe UI", 8, "bold"),
        ).pack(side="left")

        self._pet_advice_lbl = tk.Label(
            pet_box,
            text='"Checking the skies and clock for you! ♡"',
            bg=bg_grid,
            fg=fg_main,
            font=("Segoe UI", 8, "italic"),
            wraplength=310,
            justify="left",
            anchor="w",
        )
        self._pet_advice_lbl.pack(fill="x", pady=(3, 6))

        action_row = tk.Frame(pet_box, bg=bg_grid)
        action_row.pack(fill="x")

        self._say_btn = tk.Button(
            action_row,
            text="💬 Say Weather & Time",
            bg=acc,
            fg=fg_white,
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=10,
            pady=3,
            command=self.say_weather_in_bubble,
        )
        self._say_btn.pack(side="left")

        is_startup = bool(saved_data.get("weather_startup_alert", True))
        self._startup_var = tk.BooleanVar(value=is_startup)

        def _on_toggle_startup():
            d = self.get_data()
            d["weather_startup_alert"] = self._startup_var.get()
            self.save_data(d)

        cb = tk.Checkbutton(
            action_row,
            text="Startup Alert",
            variable=self._startup_var,
            command=_on_toggle_startup,
            bg=bg_grid,
            fg=fg_dim,
            selectcolor=bg_card,
            activebackground=bg_grid,
            activeforeground=fg_main,
            font=("Segoe UI", 7),
            bd=0,
            highlightthickness=0,
        )
        cb.pack(side="right")

        if self.cached_weather:
            self._render_weather_data(self.cached_weather)

        if self.win and self._canvas:
            self._bind_mousewheel(self.win, self._canvas)

    # ── Tab 2: World Clocks & Weather ────────────────────────────────────────
    def _render_world_clock_tab(self):
        if not self._body_container:
            return
        t = themes.get()
        bg_card = t.get("bg_card", "#20222e")
        bg_grid = t.get("bg_grid", "#181924")
        acc = t.get("accent", "#e74c3c")
        btn_bg = t.get("btn", "#2c2e3f")
        fg_main = t.get("fg_main", "#ffffff")
        fg_dim = t.get("fg_dim", "#888888")
        fg_white = t.get("fg_white", "#ffffff")

        top_bar = tk.Frame(self._body_container, bg=bg_card)
        top_bar.pack(fill="x", pady=(0, 6))

        tk.Label(
            top_bar,
            text="SAVED WORLD CLOCKS & WEATHER",
            bg=bg_card,
            fg=fg_dim,
            font=("Segoe UI", 8, "bold"),
        ).pack(side="left")

        tk.Button(
            top_bar,
            text="＋ Add Country",
            bg=acc,
            fg=fg_white,
            relief="flat",
            bd=0,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
            padx=8,
            pady=2,
            command=lambda: self._open_country_picker(for_world_clock=True),
        ).pack(side="right")

        # Scrollable container for world clock rows
        scroll_container = tk.Frame(self._body_container, bg=bg_card)
        scroll_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_container, bg=bg_card, highlightthickness=0)
        sb = tk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)

        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._clock_rows_frame = tk.Frame(canvas, bg=bg_card)
        frame_id = canvas.create_window((0, 0), window=self._clock_rows_frame, anchor="nw")

        def _on_cfg(e: Any):
            if canvas.winfo_exists():
                canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_c_cfg(e: Any):
            if canvas.winfo_exists():
                canvas.itemconfig(frame_id, width=max(10, e.width))

        self._clock_rows_frame.bind("<Configure>", _on_cfg)
        canvas.bind("<Configure>", _on_c_cfg)

        data = self.get_data()
        cities = list(data.get("world_clock_cities", list(DEFAULT_CITIES)))
        unit = data.get("weather_unit", "celsius")

        self._clock_row_items = []

        if not cities:
            tk.Label(
                self._clock_rows_frame,
                text="No world clocks saved yet.\nClick '＋ Add Country' to add one!",
                bg=bg_card,
                fg=fg_dim,
                font=("Segoe UI", 9),
                pady=40,
            ).pack(fill="both", expand=True)
        else:
            for city_name in cities:
                # Find timezone info
                _iana, offset_h = _TZ_MAP.get(city_name, ("UTC", 0.0))

                c_tz = timezone(timedelta(hours=offset_h))
                c_now = datetime.now(c_tz)

                row = tk.Frame(self._clock_rows_frame, bg=bg_grid, padx=10, pady=8)
                row.pack(fill="x", pady=(0, 6))

                # Left Info: City Name & Date
                left_f = tk.Frame(row, bg=bg_grid)
                left_f.pack(side="left", fill="y")

                # Parse country/city for clean display
                display_title = city_name
                if "(" in city_name and city_name.endswith(")"):
                    cntry = city_name.split("(")[0].strip()
                    cty = city_name.split("(")[1].rstrip(")").split("/")[0].split("-")[0].strip()
                    display_title = f"{cty}, {cntry}"

                c_lbl = tk.Label(
                    left_f,
                    text=display_title,
                    bg=bg_grid,
                    fg=fg_main,
                    font=("Segoe UI", 9, "bold"),
                    anchor="w",
                )
                c_lbl.pack(anchor="w")

                d_lbl = tk.Label(
                    left_f,
                    text=c_now.strftime("%a, %d %b"),
                    bg=bg_grid,
                    fg=fg_dim,
                    font=("Segoe UI", 7),
                    anchor="w",
                )
                d_lbl.pack(anchor="w")

                # Right Controls: Remove button & Weather/Time Info
                del_btn = tk.Label(
                    row,
                    text="✕",
                    bg=bg_grid,
                    fg=fg_dim,
                    font=("Segoe UI", 9, "bold"),
                    cursor="hand2",
                    padx=4,
                )
                del_btn.pack(side="right", padx=(6, 0))
                del_btn.bind("<Button-1>", lambda e, c=city_name: self._remove_world_city(c))

                # Weather Badge (Clickable to switch to full weather view!)
                w_badge = tk.Button(
                    row,
                    text="⏳ --°",
                    bg=btn_bg,
                    fg=fg_main,
                    relief="flat",
                    bd=0,
                    font=("Segoe UI", 8, "bold"),
                    cursor="hand2",
                    padx=6,
                    pady=2,
                    command=lambda c=city_name: self._select_city_for_weather(c),
                )
                w_badge.pack(side="right", padx=(8, 0))

                t_lbl = tk.Label(
                    row,
                    text=c_now.strftime("%I:%M:%S %p"),
                    bg=bg_grid,
                    fg=acc,
                    font=("Segoe UI", 10, "bold"),
                    anchor="e",
                )
                t_lbl.pack(side="right")

                item_record = {
                    "city": city_name,
                    "offset_hours": offset_h,
                    "time_lbl": t_lbl,
                    "date_lbl": d_lbl,
                    "weather_badge": w_badge,
                }
                self._clock_row_items.append(item_record)

                # Fetch/Apply Weather for Badge
                self._load_city_badge_weather(city_name, w_badge, unit)

        if self.win:
            self._bind_mousewheel(self.win, canvas)

    def _remove_world_city(self, city_name: str):
        data = self.get_data()
        cities = list(data.get("world_clock_cities", list(DEFAULT_CITIES)))
        if city_name in cities:
            cities.remove(city_name)
        data["world_clock_cities"] = cities
        self.save_data(data)
        self._render_world_clock_tab()

    def _select_city_for_weather(self, city_name: str):
        """When user clicks a world clock row weather badge, open full weather tab."""
        data = self.get_data()
        data["weather_city"] = city_name
        self.save_data(data)
        self._switch_tab("weather")
        self._fetch_weather(city_override=city_name)

    def _load_city_badge_weather(self, city_name: str, badge_btn: tk.Button, unit: str):
        if city_name in self._world_weather_cache:
            c_data = self._world_weather_cache[city_name]
            badge_btn.configure(text=f"{c_data['icon']} {c_data['temp']}{c_data['unit']}")
            return

        def task():
            res, _ = fetch_weather_sync(city_name, unit)
            if res and badge_btn.winfo_exists():
                self._world_weather_cache[city_name] = res
                self.root.after(0, lambda: badge_btn.configure(
                    text=f"{res['icon']} {res['temp']}{res['unit']}"
                ) if badge_btn.winfo_exists() else None)

        threading.Thread(target=task, daemon=True).start()

    # ── Mousewheel & Drag Handlers ───────────────────────────────────────────
    def _bind_mousewheel(self, widget: tk.Misc, canvas: tk.Canvas):
        def _on_wheel(e: Any):
            if self._hourly_canvas and self._hourly_canvas.winfo_exists():
                try:
                    w = widget.winfo_containing(e.x_root, e.y_root)
                    curr = w
                    while curr:
                        if curr == self._hourly_canvas or curr == self._hourly_frame:
                            return "break"
                        curr = getattr(curr, "master", None)
                except Exception:
                    pass

            if canvas.winfo_exists():
                delta = getattr(e, "delta", 0)
                if delta:
                    canvas.yview_scroll(int(-1 * (delta / 120)), "units")
        try:
            widget.bind("<MouseWheel>", _on_wheel, add="+")
        except Exception:
            pass
        for child in widget.winfo_children():
            self._bind_mousewheel(child, canvas)

    def _drag_start(self, event):
        if self.win and self.win.winfo_exists():
            self._dx = event.x_root - self.win.winfo_x()
            self._dy = event.y_root - self.win.winfo_y()

    def _drag_move(self, event):
        if self.win and self.win.winfo_exists():
            self.win.geometry(f"+{event.x_root - self._dx}+{event.y_root - self._dy}")
