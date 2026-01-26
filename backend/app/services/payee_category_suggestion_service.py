"""
Payee Category Suggestion Service - Suggests categories for payees based on keywords.

Similar to how PayeeIconService suggests emojis, this service analyzes payee names
and suggests appropriate categories based on keyword matching.
"""
import re
from typing import Optional, Dict, Tuple, List
from difflib import SequenceMatcher


class PayeeCategorySuggestionService:
    """
    Service for suggesting categories for payees based on keywords in their name.

    Uses comprehensive keyword mappings to intelligently suggest categories
    for payees that aren't in the known_merchants.json file.
    """

    # Category keyword mappings
    # Format: "keyword": "category_name"
    # Categories use common names that will be matched via find_category_by_name()
    CATEGORY_MAPPINGS: Dict[str, str] = {
        # ============================================================
        # RESTAURANTS & DINING
        # ============================================================
        # Fast Food
        "mcdonalds": "Restaurants",
        "mcdonald's": "Restaurants",
        "burger king": "Restaurants",
        "wendys": "Restaurants",
        "wendy's": "Restaurants",
        "taco bell": "Restaurants",
        "tacobell": "Restaurants",
        "chipotle": "Restaurants",
        "subway": "Restaurants",
        "chick-fil-a": "Restaurants",
        "chickfila": "Restaurants",
        "popeyes": "Restaurants",
        "kfc": "Restaurants",
        "pizza hut": "Restaurants",
        "dominos": "Restaurants",
        "domino's": "Restaurants",
        "papa johns": "Restaurants",
        "little caesars": "Restaurants",
        "five guys": "Restaurants",
        "shake shack": "Restaurants",
        "in-n-out": "Restaurants",
        "whataburger": "Restaurants",
        "sonic": "Restaurants",
        "arbys": "Restaurants",
        "arby's": "Restaurants",
        "jack in the box": "Restaurants",
        "del taco": "Restaurants",
        "panda express": "Restaurants",
        "wingstop": "Restaurants",
        "buffalo wild wings": "Restaurants",
        "zaxbys": "Restaurants",
        "zaxby's": "Restaurants",
        "raising canes": "Restaurants",
        "cane's": "Restaurants",
        "culvers": "Restaurants",
        "culver's": "Restaurants",
        "cook out": "Restaurants",
        "cookout": "Restaurants",
        "firehouse subs": "Restaurants",
        "jersey mikes": "Restaurants",
        "jersey mike's": "Restaurants",
        "jimmy johns": "Restaurants",
        "jimmy john's": "Restaurants",
        "potbelly": "Restaurants",
        "panera": "Restaurants",
        "noodles": "Restaurants",
        "qdoba": "Restaurants",
        "moes": "Restaurants",
        "moe's": "Restaurants",

        # Sit-Down Restaurants
        "applebees": "Restaurants",
        "applebee's": "Restaurants",
        "olive garden": "Restaurants",
        "red lobster": "Restaurants",
        "outback": "Restaurants",
        "texas roadhouse": "Restaurants",
        "longhorn": "Restaurants",
        "cracker barrel": "Restaurants",
        "cheesecake factory": "Restaurants",
        "dennys": "Restaurants",
        "denny's": "Restaurants",
        "ihop": "Restaurants",
        "waffle house": "Restaurants",
        "chilis": "Restaurants",
        "chili's": "Restaurants",
        "tgi fridays": "Restaurants",
        "red robin": "Restaurants",
        "buffalo grill": "Restaurants",
        "hooters": "Restaurants",
        "bjs restaurant": "Restaurants",
        "cheddar's": "Restaurants",
        "golden corral": "Restaurants",

        # Generic restaurant keywords
        "restaurant": "Restaurants",
        "cafe": "Restaurants",
        "diner": "Restaurants",
        "bistro": "Restaurants",
        "grill": "Restaurants",
        "kitchen": "Restaurants",
        "eatery": "Restaurants",
        "tavern": "Restaurants",
        "pub": "Restaurants",
        "cantina": "Restaurants",
        "trattoria": "Restaurants",
        "pizzeria": "Restaurants",
        "steakhouse": "Restaurants",
        "sushi": "Restaurants",
        "ramen": "Restaurants",
        "pho": "Restaurants",
        "thai": "Restaurants",
        "chinese": "Restaurants",
        "mexican": "Restaurants",
        "italian": "Restaurants",
        "indian": "Restaurants",
        "japanese": "Restaurants",
        "korean": "Restaurants",
        "vietnamese": "Restaurants",
        "mediterranean": "Restaurants",
        "greek": "Restaurants",
        "bbq": "Restaurants",
        "barbecue": "Restaurants",
        "wings": "Restaurants",
        "seafood": "Restaurants",
        "taqueria": "Restaurants",
        "burrito": "Restaurants",
        "taco": "Restaurants",
        "burger": "Restaurants",
        "pizza": "Restaurants",
        "bakery": "Restaurants",
        "bagel": "Restaurants",
        "deli": "Restaurants",
        "sandwich": "Restaurants",
        "sub shop": "Restaurants",
        "food truck": "Restaurants",
        "catering": "Restaurants",

        # ============================================================
        # COFFEE & BEVERAGES
        # ============================================================
        "starbucks": "Coffee Shops",
        "dunkin": "Coffee Shops",
        "peets": "Coffee Shops",
        "peet's": "Coffee Shops",
        "caribou coffee": "Coffee Shops",
        "tim hortons": "Coffee Shops",
        "dutch bros": "Coffee Shops",
        "coffee bean": "Coffee Shops",
        "philz": "Coffee Shops",
        "blue bottle": "Coffee Shops",
        "intelligentsia": "Coffee Shops",
        "la colombe": "Coffee Shops",
        "scooters coffee": "Coffee Shops",
        "black rifle": "Coffee Shops",
        "coffee": "Coffee Shops",
        "espresso": "Coffee Shops",
        "latte": "Coffee Shops",
        "cappuccino": "Coffee Shops",
        "boba": "Coffee Shops",
        "bubble tea": "Coffee Shops",
        "tea house": "Coffee Shops",
        "smoothie": "Coffee Shops",
        "juice bar": "Coffee Shops",
        "jamba": "Coffee Shops",
        "smoothie king": "Coffee Shops",
        "tropical smoothie": "Coffee Shops",

        # ============================================================
        # GROCERIES
        # ============================================================
        "walmart": "Groceries",
        "kroger": "Groceries",
        "safeway": "Groceries",
        "albertsons": "Groceries",
        "publix": "Groceries",
        "trader joes": "Groceries",
        "trader joe's": "Groceries",
        "whole foods": "Groceries",
        "wholefoods": "Groceries",
        "aldi": "Groceries",
        "lidl": "Groceries",
        "costco": "Groceries",
        "sams club": "Groceries",
        "sam's club": "Groceries",
        "bjs wholesale": "Groceries",
        "heb": "Groceries",
        "h-e-b": "Groceries",
        "meijer": "Groceries",
        "wegmans": "Groceries",
        "food lion": "Groceries",
        "giant": "Groceries",
        "stop shop": "Groceries",
        "stop & shop": "Groceries",
        "sprouts": "Groceries",
        "fresh market": "Groceries",
        "natural grocers": "Groceries",
        "market basket": "Groceries",
        "winco": "Groceries",
        "piggly wiggly": "Groceries",
        "food city": "Groceries",
        "schnucks": "Groceries",
        "hy-vee": "Groceries",
        "hyvee": "Groceries",
        "harris teeter": "Groceries",
        "shoprite": "Groceries",
        "acme": "Groceries",
        "vons": "Groceries",
        "ralphs": "Groceries",
        "fred meyer": "Groceries",
        "king soopers": "Groceries",
        "jewel osco": "Groceries",
        "grocery": "Groceries",
        "supermarket": "Groceries",
        "market": "Groceries",
        "food store": "Groceries",
        "produce": "Groceries",
        "butcher": "Groceries",
        "meat market": "Groceries",
        "fish market": "Groceries",

        # ============================================================
        # GAS & FUEL
        # ============================================================
        "shell": "Gas & Fuel",
        "exxon": "Gas & Fuel",
        "exxonmobil": "Gas & Fuel",
        "chevron": "Gas & Fuel",
        "bp": "Gas & Fuel",
        "texaco": "Gas & Fuel",
        "76": "Gas & Fuel",
        "marathon": "Gas & Fuel",
        "citgo": "Gas & Fuel",
        "sunoco": "Gas & Fuel",
        "valero": "Gas & Fuel",
        "phillips 66": "Gas & Fuel",
        "conoco": "Gas & Fuel",
        "sinclair": "Gas & Fuel",
        "caseys": "Gas & Fuel",
        "casey's": "Gas & Fuel",
        "quiktrip": "Gas & Fuel",
        "qt": "Gas & Fuel",
        "wawa": "Gas & Fuel",
        "sheetz": "Gas & Fuel",
        "racetrac": "Gas & Fuel",
        "loves": "Gas & Fuel",
        "love's": "Gas & Fuel",
        "pilot": "Gas & Fuel",
        "flying j": "Gas & Fuel",
        "ta travel": "Gas & Fuel",
        "speedway": "Gas & Fuel",
        "7-eleven": "Gas & Fuel",
        "7eleven": "Gas & Fuel",
        "circle k": "Gas & Fuel",
        "cumberland farms": "Gas & Fuel",
        "kum go": "Gas & Fuel",
        "kum & go": "Gas & Fuel",
        "maverick": "Gas & Fuel",
        "murphy": "Gas & Fuel",
        "murphy usa": "Gas & Fuel",
        "kwik trip": "Gas & Fuel",
        "kwik star": "Gas & Fuel",
        "gas": "Gas & Fuel",
        "fuel": "Gas & Fuel",
        "petrol": "Gas & Fuel",
        "petroleum": "Gas & Fuel",
        "gasoline": "Gas & Fuel",
        "diesel": "Gas & Fuel",
        "filling station": "Gas & Fuel",
        "service station": "Gas & Fuel",

        # ============================================================
        # AUTO & TRANSPORT
        # ============================================================
        # Rideshare
        "uber": "Transportation",
        "lyft": "Transportation",
        "waymo": "Transportation",

        # Car rental
        "enterprise": "Transportation",
        "hertz": "Transportation",
        "avis": "Transportation",
        "budget rent": "Transportation",
        "national car": "Transportation",
        "dollar rent": "Transportation",
        "thrifty": "Transportation",
        "alamo": "Transportation",
        "turo": "Transportation",
        "zipcar": "Transportation",

        # Public transit
        "metro": "Transportation",
        "subway": "Transportation",
        "transit": "Transportation",
        "bus": "Transportation",
        "train": "Transportation",
        "amtrak": "Transportation",
        "greyhound": "Transportation",
        "megabus": "Transportation",

        # Parking & tolls
        "parking": "Auto & Transport",
        "garage": "Auto & Transport",
        "meter": "Auto & Transport",
        "toll": "Auto & Transport",
        "ez pass": "Auto & Transport",
        "fastrak": "Auto & Transport",
        "sunpass": "Auto & Transport",

        # Auto services
        "autozone": "Auto & Transport",
        "advance auto": "Auto & Transport",
        "oreilly": "Auto & Transport",
        "o'reilly": "Auto & Transport",
        "napa": "Auto & Transport",
        "pep boys": "Auto & Transport",
        "jiffy lube": "Auto & Transport",
        "valvoline": "Auto & Transport",
        "firestone": "Auto & Transport",
        "goodyear": "Auto & Transport",
        "discount tire": "Auto & Transport",
        "belle tire": "Auto & Transport",
        "midas": "Auto & Transport",
        "maaco": "Auto & Transport",
        "safelite": "Auto & Transport",
        "meineke": "Auto & Transport",
        "car wash": "Auto & Transport",
        "carwash": "Auto & Transport",
        "detailing": "Auto & Transport",
        "oil change": "Auto & Transport",
        "tire": "Auto & Transport",
        "automotive": "Auto & Transport",
        "mechanic": "Auto & Transport",
        "auto repair": "Auto & Transport",
        "auto parts": "Auto & Transport",
        "body shop": "Auto & Transport",
        "collision": "Auto & Transport",
        "transmission": "Auto & Transport",
        "brake": "Auto & Transport",
        "alignment": "Auto & Transport",
        "smog": "Auto & Transport",
        "emissions": "Auto & Transport",
        "inspection": "Auto & Transport",
        "dmv": "Auto & Transport",

        # ============================================================
        # ENTERTAINMENT & STREAMING
        # ============================================================
        "netflix": "Entertainment",
        "disney+": "Entertainment",
        "disneyplus": "Entertainment",
        "hulu": "Entertainment",
        "hbo": "Entertainment",
        "max": "Entertainment",
        "amazon prime": "Entertainment",
        "prime video": "Entertainment",
        "apple tv": "Entertainment",
        "peacock": "Entertainment",
        "paramount": "Entertainment",
        "paramount+": "Entertainment",
        "youtube": "Entertainment",
        "youtube tv": "Entertainment",
        "spotify": "Entertainment",
        "apple music": "Entertainment",
        "amazon music": "Entertainment",
        "pandora": "Entertainment",
        "tidal": "Entertainment",
        "deezer": "Entertainment",
        "soundcloud": "Entertainment",
        "audible": "Entertainment",
        "kindle": "Entertainment",
        "scribd": "Entertainment",
        "xbox": "Entertainment",
        "playstation": "Entertainment",
        "ps plus": "Entertainment",
        "nintendo": "Entertainment",
        "steam": "Entertainment",
        "epic games": "Entertainment",
        "twitch": "Entertainment",
        "discord": "Entertainment",
        "crunchyroll": "Entertainment",
        "funimation": "Entertainment",
        "sling": "Entertainment",
        "fubo": "Entertainment",
        "philo": "Entertainment",
        "espn+": "Entertainment",
        "espn": "Entertainment",
        "movie": "Entertainment",
        "movies": "Entertainment",
        "cinema": "Entertainment",
        "theater": "Entertainment",
        "theatre": "Entertainment",
        "amc": "Entertainment",
        "regal": "Entertainment",
        "cinemark": "Entertainment",
        "concert": "Entertainment",
        "ticketmaster": "Entertainment",
        "stubhub": "Entertainment",
        "seatgeek": "Entertainment",
        "eventbrite": "Entertainment",
        "live nation": "Entertainment",
        "bowling": "Entertainment",
        "arcade": "Entertainment",
        "dave busters": "Entertainment",
        "dave & busters": "Entertainment",
        "main event": "Entertainment",
        "topgolf": "Entertainment",
        "zoo": "Entertainment",
        "aquarium": "Entertainment",
        "museum": "Entertainment",
        "theme park": "Entertainment",
        "amusement": "Entertainment",

        # ============================================================
        # SHOPPING
        # ============================================================
        "target": "Shopping",
        "amazon": "Shopping",
        "ebay": "Shopping",
        "etsy": "Shopping",
        "best buy": "Shopping",
        "bestbuy": "Shopping",
        "home depot": "Shopping",
        "homedepot": "Shopping",
        "lowes": "Shopping",
        "lowe's": "Shopping",
        "ikea": "Shopping",
        "wayfair": "Shopping",
        "overstock": "Shopping",
        "nordstrom": "Shopping",
        "macys": "Shopping",
        "macy's": "Shopping",
        "kohls": "Shopping",
        "kohl's": "Shopping",
        "tj maxx": "Shopping",
        "tjmaxx": "Shopping",
        "marshalls": "Shopping",
        "ross": "Shopping",
        "dollar general": "Shopping",
        "dollar tree": "Shopping",
        "five below": "Shopping",
        "big lots": "Shopping",
        "bed bath": "Shopping",
        "williams sonoma": "Shopping",
        "pottery barn": "Shopping",
        "crate barrel": "Shopping",
        "newegg": "Shopping",
        "zappos": "Shopping",
        "chewy": "Shopping",
        "petco": "Shopping",
        "petsmart": "Shopping",
        "gamestop": "Shopping",
        "sephora": "Shopping",
        "ulta": "Shopping",
        "bath body works": "Shopping",
        "victorias secret": "Shopping",
        "gap": "Shopping",
        "old navy": "Shopping",
        "banana republic": "Shopping",
        "h&m": "Shopping",
        "zara": "Shopping",
        "uniqlo": "Shopping",
        "nike": "Shopping",
        "adidas": "Shopping",
        "under armour": "Shopping",
        "lululemon": "Shopping",
        "rei": "Shopping",
        "dicks sporting": "Shopping",
        "academy sports": "Shopping",
        "cabelas": "Shopping",
        "bass pro": "Shopping",
        "michaels": "Shopping",
        "joann": "Shopping",
        "hobby lobby": "Shopping",
        "office depot": "Shopping",
        "staples": "Shopping",
        "shop": "Shopping",
        "store": "Shopping",
        "outlet": "Shopping",
        "mall": "Shopping",
        "boutique": "Shopping",
        "retail": "Shopping",
        "merchandise": "Shopping",

        # ============================================================
        # HEALTH & MEDICAL
        # ============================================================
        "cvs": "Health & Medical",
        "walgreens": "Health & Medical",
        "rite aid": "Health & Medical",
        "pharmacy": "Health & Medical",
        "drugstore": "Health & Medical",
        "hospital": "Health & Medical",
        "clinic": "Health & Medical",
        "medical": "Health & Medical",
        "doctor": "Health & Medical",
        "physician": "Health & Medical",
        "urgent care": "Health & Medical",
        "emergency": "Health & Medical",
        "dental": "Health & Medical",
        "dentist": "Health & Medical",
        "orthodontist": "Health & Medical",
        "optometrist": "Health & Medical",
        "eye doctor": "Health & Medical",
        "vision": "Health & Medical",
        "optical": "Health & Medical",
        "glasses": "Health & Medical",
        "lenscrafters": "Health & Medical",
        "warby parker": "Health & Medical",
        "mental health": "Health & Medical",
        "therapy": "Health & Medical",
        "counseling": "Health & Medical",
        "psychiatry": "Health & Medical",
        "psychology": "Health & Medical",
        "chiropractor": "Health & Medical",
        "physical therapy": "Health & Medical",
        "lab": "Health & Medical",
        "laboratory": "Health & Medical",
        "quest diagnostics": "Health & Medical",
        "labcorp": "Health & Medical",
        "imaging": "Health & Medical",
        "radiology": "Health & Medical",
        "dermatology": "Health & Medical",
        "cardiology": "Health & Medical",
        "pediatric": "Health & Medical",
        "wellness": "Health & Medical",
        "goodrx": "Health & Medical",
        "zocdoc": "Health & Medical",
        "betterhelp": "Health & Medical",
        "talkspace": "Health & Medical",

        # ============================================================
        # FITNESS & GYM
        # ============================================================
        "planet fitness": "Gym & Fitness",
        "la fitness": "Gym & Fitness",
        "equinox": "Gym & Fitness",
        "orangetheory": "Gym & Fitness",
        "crossfit": "Gym & Fitness",
        "24 hour fitness": "Gym & Fitness",
        "anytime fitness": "Gym & Fitness",
        "golds gym": "Gym & Fitness",
        "gold's gym": "Gym & Fitness",
        "lifetime fitness": "Gym & Fitness",
        "ymca": "Gym & Fitness",
        "ywca": "Gym & Fitness",
        "peloton": "Gym & Fitness",
        "fitbit": "Gym & Fitness",
        "strava": "Gym & Fitness",
        "myfitnesspal": "Gym & Fitness",
        "noom": "Gym & Fitness",
        "weight watchers": "Gym & Fitness",
        "gym": "Gym & Fitness",
        "fitness": "Gym & Fitness",
        "workout": "Gym & Fitness",
        "yoga": "Gym & Fitness",
        "pilates": "Gym & Fitness",
        "spin": "Gym & Fitness",
        "cycling": "Gym & Fitness",
        "martial arts": "Gym & Fitness",
        "boxing": "Gym & Fitness",
        "mma": "Gym & Fitness",
        "personal training": "Gym & Fitness",
        "trainer": "Gym & Fitness",

        # ============================================================
        # UTILITIES
        # ============================================================
        "electric": "Utilities",
        "power": "Utilities",
        "energy": "Utilities",
        "gas utility": "Utilities",
        "natural gas": "Utilities",
        "water": "Utilities",
        "sewer": "Utilities",
        "trash": "Utilities",
        "garbage": "Utilities",
        "waste management": "Utilities",
        "republic services": "Utilities",
        "utility": "Utilities",
        "utilities": "Utilities",

        # ============================================================
        # PHONE & INTERNET
        # ============================================================
        "verizon": "Phone & Internet",
        "at&t": "Phone & Internet",
        "att": "Phone & Internet",
        "t-mobile": "Phone & Internet",
        "tmobile": "Phone & Internet",
        "sprint": "Phone & Internet",
        "xfinity": "Phone & Internet",
        "comcast": "Phone & Internet",
        "spectrum": "Phone & Internet",
        "cox": "Phone & Internet",
        "frontier": "Phone & Internet",
        "centurylink": "Phone & Internet",
        "lumen": "Phone & Internet",
        "google fi": "Phone & Internet",
        "mint mobile": "Phone & Internet",
        "visible": "Phone & Internet",
        "cricket": "Phone & Internet",
        "boost mobile": "Phone & Internet",
        "metro pcs": "Phone & Internet",
        "us cellular": "Phone & Internet",
        "straight talk": "Phone & Internet",
        "tracfone": "Phone & Internet",
        "phone": "Phone & Internet",
        "cellular": "Phone & Internet",
        "mobile": "Phone & Internet",
        "wireless": "Phone & Internet",
        "internet": "Phone & Internet",
        "wifi": "Phone & Internet",
        "broadband": "Phone & Internet",
        "cable": "Phone & Internet",
        "fiber": "Phone & Internet",

        # ============================================================
        # INSURANCE
        # ============================================================
        "geico": "Insurance",
        "progressive": "Insurance",
        "state farm": "Insurance",
        "allstate": "Insurance",
        "liberty mutual": "Insurance",
        "farmers": "Insurance",
        "nationwide": "Insurance",
        "usaa": "Insurance",
        "travelers": "Insurance",
        "aetna": "Insurance",
        "cigna": "Insurance",
        "united healthcare": "Insurance",
        "blue cross": "Insurance",
        "bcbs": "Insurance",
        "anthem": "Insurance",
        "humana": "Insurance",
        "kaiser": "Insurance",
        "metlife": "Insurance",
        "prudential": "Insurance",
        "aflac": "Insurance",
        "lemonade": "Insurance",
        "insurance": "Insurance",

        # ============================================================
        # TRAVEL & HOTELS
        # ============================================================
        "airbnb": "Travel",
        "vrbo": "Travel",
        "booking.com": "Travel",
        "expedia": "Travel",
        "hotels.com": "Travel",
        "kayak": "Travel",
        "priceline": "Travel",
        "trivago": "Travel",
        "tripadvisor": "Travel",
        "marriott": "Travel",
        "hilton": "Travel",
        "hyatt": "Travel",
        "ihg": "Travel",
        "holiday inn": "Travel",
        "wyndham": "Travel",
        "best western": "Travel",
        "choice hotels": "Travel",
        "comfort inn": "Travel",
        "hampton inn": "Travel",
        "doubletree": "Travel",
        "motel 6": "Travel",
        "super 8": "Travel",
        "la quinta": "Travel",
        "hotel": "Travel",
        "motel": "Travel",
        "resort": "Travel",
        "lodging": "Travel",
        "inn": "Travel",

        # Airlines
        "american airlines": "Travel",
        "delta": "Travel",
        "united": "Travel",
        "southwest": "Travel",
        "jetblue": "Travel",
        "alaska airlines": "Travel",
        "spirit": "Travel",
        "frontier airlines": "Travel",
        "airline": "Travel",
        "flight": "Travel",
        "airport": "Travel",

        # ============================================================
        # PERSONAL CARE
        # ============================================================
        "salon": "Personal Care",
        "spa": "Personal Care",
        "barber": "Personal Care",
        "hair": "Personal Care",
        "nail": "Personal Care",
        "manicure": "Personal Care",
        "pedicure": "Personal Care",
        "massage": "Personal Care",
        "facial": "Personal Care",
        "waxing": "Personal Care",
        "beauty": "Personal Care",
        "cosmetic": "Personal Care",
        "grooming": "Personal Care",
        "haircut": "Personal Care",
        "supercuts": "Personal Care",
        "great clips": "Personal Care",
        "sports clips": "Personal Care",
        "floyd's": "Personal Care",
        "dry bar": "Personal Care",
        "drybar": "Personal Care",

        # ============================================================
        # EDUCATION
        # ============================================================
        "school": "Education",
        "university": "Education",
        "college": "Education",
        "tuition": "Education",
        "course": "Education",
        "class": "Education",
        "tutoring": "Education",
        "coursera": "Education",
        "udemy": "Education",
        "skillshare": "Education",
        "masterclass": "Education",
        "linkedin learning": "Education",
        "duolingo": "Education",
        "rosetta stone": "Education",
        "babbel": "Education",
        "khan academy": "Education",
        "chegg": "Education",
        "quizlet": "Education",
        "grammarly": "Education",
        "education": "Education",

        # ============================================================
        # SUBSCRIPTIONS & SOFTWARE
        # ============================================================
        "adobe": "Subscriptions",
        "microsoft": "Subscriptions",
        "apple": "Subscriptions",
        "google": "Subscriptions",
        "dropbox": "Subscriptions",
        "box": "Subscriptions",
        "github": "Subscriptions",
        "gitlab": "Subscriptions",
        "atlassian": "Subscriptions",
        "jira": "Subscriptions",
        "slack": "Subscriptions",
        "zoom": "Subscriptions",
        "1password": "Subscriptions",
        "lastpass": "Subscriptions",
        "bitwarden": "Subscriptions",
        "nordvpn": "Subscriptions",
        "expressvpn": "Subscriptions",
        "norton": "Subscriptions",
        "mcafee": "Subscriptions",
        "notion": "Subscriptions",
        "evernote": "Subscriptions",
        "subscription": "Subscriptions",
        "software": "Subscriptions",
        "saas": "Subscriptions",
        "app": "Subscriptions",

        # ============================================================
        # FEES & FINANCE
        # ============================================================
        "bank": "Fees & Charges",
        "banking": "Fees & Charges",
        "atm": "Fees & Charges",
        "fee": "Fees & Charges",
        "charge": "Fees & Charges",
        "service charge": "Fees & Charges",
        "overdraft": "Fees & Charges",
        "nsf": "Fees & Charges",
        "maintenance": "Fees & Charges",

        # ============================================================
        # GIFTS & DONATIONS
        # ============================================================
        "charity": "Gifts & Donations",
        "donation": "Gifts & Donations",
        "nonprofit": "Gifts & Donations",
        "church": "Gifts & Donations",
        "religious": "Gifts & Donations",
        "tithe": "Gifts & Donations",
        "gift": "Gifts & Donations",
        "gofundme": "Gifts & Donations",
        "patreon": "Gifts & Donations",

        # ============================================================
        # PETS
        # ============================================================
        "pet": "Pets",
        "veterinary": "Pets",
        "vet": "Pets",
        "animal hospital": "Pets",
        "pet supplies": "Pets",
        "dog": "Pets",
        "cat": "Pets",
        "groomer": "Pets",
        "pet grooming": "Pets",
        "banfield": "Pets",
        "vca": "Pets",
        "rover": "Pets",
        "wag": "Pets",

        # ============================================================
        # CHILDCARE & KIDS
        # ============================================================
        "daycare": "Childcare",
        "childcare": "Childcare",
        "preschool": "Childcare",
        "nursery": "Childcare",
        "nanny": "Childcare",
        "babysitter": "Childcare",
        "kids": "Childcare",
        "children": "Childcare",
        "camp": "Childcare",
        "afterschool": "Childcare",

        # ============================================================
        # HOME SERVICES
        # ============================================================
        "cleaning": "Home Services",
        "housekeeping": "Home Services",
        "maid": "Home Services",
        "landscaping": "Home Services",
        "lawn": "Home Services",
        "pool": "Home Services",
        "pest control": "Home Services",
        "exterminator": "Home Services",
        "plumber": "Home Services",
        "plumbing": "Home Services",
        "electrician": "Home Services",
        "hvac": "Home Services",
        "contractor": "Home Services",
        "handyman": "Home Services",
        "repair": "Home Services",
        "renovation": "Home Services",
        "remodel": "Home Services",
        "moving": "Home Services",
        "storage": "Home Services",
        "security": "Home Services",
        "adt": "Home Services",
        "vivint": "Home Services",
        "simplisafe": "Home Services",
        "ring": "Home Services",

        # ============================================================
        # TAXES & LEGAL
        # ============================================================
        "tax": "Taxes",
        "irs": "Taxes",
        "turbotax": "Taxes",
        "h&r block": "Taxes",
        "jackson hewitt": "Taxes",
        "accounting": "Taxes",
        "cpa": "Taxes",
        "legal": "Legal",
        "lawyer": "Legal",
        "attorney": "Legal",
        "law firm": "Legal",
        "notary": "Legal",

        # ============================================================
        # DELIVERY & FOOD DELIVERY
        # ============================================================
        "doordash": "Food Delivery",
        "uber eats": "Food Delivery",
        "ubereats": "Food Delivery",
        "grubhub": "Food Delivery",
        "postmates": "Food Delivery",
        "seamless": "Food Delivery",
        "instacart": "Food Delivery",
        "gopuff": "Food Delivery",
        "shipt": "Food Delivery",
        "delivery": "Food Delivery",
    }

    # Default category when no match is found
    DEFAULT_CATEGORY = None  # Return None if we can't determine

    def __init__(self):
        """Initialize the PayeeCategorySuggestionService."""
        self._normalize_pattern = re.compile(r'[^a-z0-9\s&\'-]')
        self._whitespace_pattern = re.compile(r'\s+')

    def _normalize_name(self, name: str) -> str:
        """Normalize a payee name for matching."""
        normalized = self._normalize_pattern.sub('', name.lower())
        normalized = self._whitespace_pattern.sub(' ', normalized).strip()
        return normalized

    def suggest_category(self, payee_name: str) -> Optional[dict]:
        """
        Suggest a category for a payee based on keywords in their name.

        Returns a dict with:
        - category_name: The suggested category name (to be matched by find_category_by_name)
        - matched_term: What keyword was matched
        - confidence: Match confidence (1.0 for exact brand, lower for keyword)

        Returns None if no suitable category can be determined.
        """
        if not payee_name or len(payee_name) < 2:
            return None

        normalized = self._normalize_name(payee_name)

        # Try exact match first (for well-known brands)
        if normalized in self.CATEGORY_MAPPINGS:
            return {
                "category_name": self.CATEGORY_MAPPINGS[normalized],
                "matched_term": normalized,
                "confidence": 1.0,
            }

        # Try partial matches - check if any keyword is contained in the name
        best_match = None
        best_length = 0

        for keyword, category in self.CATEGORY_MAPPINGS.items():
            if keyword in normalized:
                # Prefer longer matches (more specific)
                if len(keyword) > best_length:
                    best_match = {
                        "category_name": category,
                        "matched_term": keyword,
                        "confidence": min(0.9, 0.6 + (len(keyword) / 20)),
                    }
                    best_length = len(keyword)

        if best_match:
            return best_match

        # Try word-by-word matching
        words = set(normalized.split())
        for keyword, category in self.CATEGORY_MAPPINGS.items():
            keyword_words = set(keyword.split())
            if keyword_words.issubset(words):
                match_length = sum(len(w) for w in keyword_words)
                if match_length > best_length:
                    best_match = {
                        "category_name": category,
                        "matched_term": keyword,
                        "confidence": 0.75,
                    }
                    best_length = match_length

        if best_match:
            return best_match

        # Check individual words
        for word in words:
            if len(word) >= 3 and word in self.CATEGORY_MAPPINGS:
                return {
                    "category_name": self.CATEGORY_MAPPINGS[word],
                    "matched_term": word,
                    "confidence": 0.6,
                }

        # Try fuzzy matching for close matches (typos, abbreviations)
        for keyword, category in self.CATEGORY_MAPPINGS.items():
            if len(keyword) >= 4:  # Only fuzzy match longer keywords
                similarity = SequenceMatcher(None, normalized, keyword).ratio()
                if similarity > 0.85:
                    return {
                        "category_name": category,
                        "matched_term": keyword,
                        "confidence": similarity,
                    }

        return None

    def get_category_name(self, payee_name: str) -> Optional[str]:
        """
        Simple method to just get the suggested category name.
        Returns None if no category can be suggested.
        """
        result = self.suggest_category(payee_name)
        return result["category_name"] if result else None


# Singleton instance for easy import
payee_category_suggestion_service = PayeeCategorySuggestionService()
