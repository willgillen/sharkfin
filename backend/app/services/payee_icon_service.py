"""
Payee Icon Service - Provides brand logo URLs and emoji fallbacks for payees.

Uses Simple Icons CDN for brand logos and a comprehensive emoji mapping system
for fallbacks when no brand logo is available.
"""
import re
from typing import Optional, Dict, Tuple
from difflib import SequenceMatcher


class PayeeIconService:
    """
    Service for suggesting icons (brand logos or emojis) for payees.

    Brand logos are served from the Simple Icons CDN.
    Emoji fallbacks are based on keyword matching against the payee name.
    """

    # Simple Icons CDN base URL
    SIMPLE_ICONS_CDN = "https://cdn.simpleicons.org"

    # Brand name to Simple Icons slug mapping (500+ brands)
    # Format: "normalized_name": ("slug", "hex_color")
    BRAND_MAPPINGS: Dict[str, Tuple[str, str]] = {
        # Major Retailers
        "walmart": ("walmart", "0071CE"),
        "target": ("target", "CC0000"),
        "costco": ("costco", "E31837"),
        "amazon": ("amazon", "FF9900"),
        "whole foods": ("wholefoods", "00674B"),
        "wholefoods": ("wholefoods", "00674B"),
        "kroger": ("kroger", "0033A0"),
        "safeway": ("safeway", "E8315B"),
        "trader joes": ("traderjoes", "C8102E"),
        "trader joe's": ("traderjoes", "C8102E"),
        "aldi": ("aldi", "00005F"),
        "publix": ("publix", "3B8544"),
        "cvs": ("cvs", "CC0000"),
        "walgreens": ("walgreens", "E31837"),
        "home depot": ("homedepot", "F96305"),
        "homedepot": ("homedepot", "F96305"),
        "lowes": ("lowes", "004990"),
        "lowe's": ("lowes", "004990"),
        "ikea": ("ikea", "0058A3"),
        "best buy": ("bestbuy", "0046BE"),
        "bestbuy": ("bestbuy", "0046BE"),
        "nordstrom": ("nordstrom", "000000"),
        "macys": ("macys", "E21A2C"),
        "macy's": ("macys", "E21A2C"),
        "kohls": ("kohls", "000000"),
        "kohl's": ("kohls", "000000"),
        "tj maxx": ("tjmaxx", "E11A2C"),
        "tjmaxx": ("tjmaxx", "E11A2C"),
        "marshalls": ("marshalls", "0A2240"),
        "ross": ("ross", "003DA5"),
        "dollar general": ("dollargeneral", "FFD000"),
        "dollar tree": ("dollartree", "00A850"),
        "five below": ("fivebelow", "002D62"),
        "big lots": ("biglots", "F26522"),
        "bed bath beyond": ("bedbathandbeyond", "003A70"),
        "williams sonoma": ("williamssonoma", "231F20"),
        "pottery barn": ("potterybarn", "8B6B4D"),
        "crate barrel": ("crateandbarrel", "000000"),
        "wayfair": ("wayfair", "7F187F"),
        "overstock": ("overstock", "D22630"),
        "etsy": ("etsy", "F16521"),
        "ebay": ("ebay", "E53238"),
        "wish": ("wish", "2FB7EC"),
        "aliexpress": ("aliexpress", "FF4747"),
        "newegg": ("newegg", "FF6600"),
        "zappos": ("zappos", "FF6900"),
        "chewy": ("chewy", "1C49C2"),
        "petco": ("petco", "0056A3"),
        "petsmart": ("petsmart", "E41837"),
        "gamestop": ("gamestop", "000000"),
        "sephora": ("sephora", "000000"),
        "ulta": ("ulta", "FC6C85"),
        "bath body works": ("bathandbodyworks", "003366"),
        "victorias secret": ("victoriassecret", "231F20"),
        "gap": ("gap", "000000"),
        "old navy": ("oldnavy", "003366"),
        "banana republic": ("bananarepublic", "2B2B2B"),
        "h&m": ("hm", "E50010"),
        "zara": ("zara", "000000"),
        "uniqlo": ("uniqlo", "FF0000"),
        "nike": ("nike", "000000"),
        "adidas": ("adidas", "000000"),
        "under armour": ("underarmour", "1D1D1D"),
        "lululemon": ("lululemon", "D31334"),
        "rei": ("rei", "000000"),
        "dicks sporting goods": ("dickssportinggoods", "006341"),
        "academy sports": ("academysportsandoutdoors", "CE0E2D"),
        "cabelas": ("cabelas", "344A38"),
        "bass pro": ("basspro", "006341"),

        # Fast Food & Restaurants
        "mcdonalds": ("mcdonalds", "FFC72C"),
        "mcdonald's": ("mcdonalds", "FFC72C"),
        "burger king": ("burgerking", "D62300"),
        "wendys": ("wendys", "E2203A"),
        "wendy's": ("wendys", "E2203A"),
        "taco bell": ("tacobell", "702082"),
        "tacobell": ("tacobell", "702082"),
        "chipotle": ("chipotle", "A81612"),
        "subway": ("subway", "00A850"),
        "chick-fil-a": ("chickfila", "E51636"),
        "chickfila": ("chickfila", "E51636"),
        "chick fil a": ("chickfila", "E51636"),
        "popeyes": ("popeyes", "F26722"),
        "kfc": ("kfc", "F40027"),
        "pizza hut": ("pizzahut", "EE3A24"),
        "pizzahut": ("pizzahut", "EE3A24"),
        "dominos": ("dominos", "006491"),
        "domino's": ("dominos", "006491"),
        "papa johns": ("papajohns", "23751A"),
        "papa john's": ("papajohns", "23751A"),
        "little caesars": ("littlecaesars", "F36F25"),
        "starbucks": ("starbucks", "006241"),
        "dunkin": ("dunkin", "FF671F"),
        "dunkin donuts": ("dunkin", "FF671F"),
        "panera": ("panerabread", "3D6637"),
        "panera bread": ("panerabread", "3D6637"),
        "five guys": ("fiveguys", "E4022C"),
        "shake shack": ("shakeshack", "0A8952"),
        "in-n-out": ("innout", "FF162C"),
        "innout": ("innout", "FF162C"),
        "in n out": ("innout", "FF162C"),
        "whataburger": ("whataburger", "FF5C00"),
        "sonic": ("sonic", "006DB7"),
        "arbys": ("arbys", "B30000"),
        "arby's": ("arbys", "B30000"),
        "jack in the box": ("jackinthebox", "E60011"),
        "del taco": ("deltaco", "00613C"),
        "panda express": ("pandaexpress", "D62629"),
        "wingstop": ("wingstop", "1D6F42"),
        "buffalo wild wings": ("buffalowildwings", "FFB81C"),
        "applebees": ("applebees", "CC1D42"),
        "applebee's": ("applebees", "CC1D42"),
        "olive garden": ("olivegarden", "88714A"),
        "red lobster": ("redlobster", "E2181B"),
        "outback": ("outbacksteakhouse", "883531"),
        "outback steakhouse": ("outbacksteakhouse", "883531"),
        "texas roadhouse": ("texasroadhouse", "EDC900"),
        "cracker barrel": ("crackerbarrel", "B4975A"),
        "dennys": ("dennys", "FEDF00"),
        "denny's": ("dennys", "FEDF00"),
        "ihop": ("ihop", "003B73"),
        "waffle house": ("wafflehouse", "F3C50C"),
        "noodles company": ("noodlesandcompany", "E31837"),
        "sweetgreen": ("sweetgreen", "2F7941"),
        "cava": ("cava", "A8824E"),
        "jersey mikes": ("jerseymikes", "B51117"),
        "jersey mike's": ("jerseymikes", "B51117"),
        "firehouse subs": ("firehousesubs", "A41623"),
        "jimmy johns": ("jimmyjohns", "000000"),
        "jimmy john's": ("jimmyjohns", "000000"),
        "potbelly": ("potbelly", "C23627"),
        "tropical smoothie": ("tropicalsmoothiecafe", "4BBF6E"),
        "jamba juice": ("jambajuice", "DA2E2E"),
        "smoothie king": ("smoothieking", "E51937"),
        "dairy queen": ("dairyqueen", "ED1C24"),
        "cold stone": ("coldstonecreamery", "00447C"),
        "baskin robbins": ("baskinrobbins", "FF1493"),
        "krispy kreme": ("krispykreme", "004B23"),
        "tim hortons": ("timhortons", "C8102E"),
        "dutch bros": ("dutchbros", "0D456A"),
        "peets": ("peets", "C6A961"),
        "peet's": ("peets", "C6A961"),
        "caribou coffee": ("cariboucoffee", "00A94F"),

        # Coffee & Beverages
        "coffee": ("buymeacoffee", "FFDD00"),
        "cafe": ("buymeacoffee", "FFDD00"),
        "espresso": ("buymeacoffee", "FFDD00"),

        # Grocery & Food
        "instacart": ("instacart", "43B02A"),
        "doordash": ("doordash", "FF3008"),
        "uber eats": ("ubereats", "06C167"),
        "ubereats": ("ubereats", "06C167"),
        "grubhub": ("grubhub", "F63440"),
        "postmates": ("postmates", "000000"),
        "seamless": ("seamless", "F47E2A"),
        "gopuff": ("gopuff", "00A9E0"),
        "shipt": ("shipt", "73C13B"),
        "blue apron": ("blueapron", "0075C9"),
        "hellofresh": ("hellofresh", "7AB648"),
        "factor": ("factor", "2D2D2D"),

        # Transportation & Ride Sharing
        "uber": ("uber", "000000"),
        "lyft": ("lyft", "FF00BF"),
        "waymo": ("waymo", "1EA362"),
        "bird": ("bird", "00D4AA"),
        "lime": ("lime", "00DD00"),
        "spin": ("spin", "FF5503"),
        "enterprise": ("enterprise", "007A33"),
        "hertz": ("hertz", "FFD900"),
        "avis": ("avis", "D71921"),
        "budget": ("budget", "F47721"),
        "national": ("nationalcar", "00843D"),
        "turo": ("turo", "00AEF0"),
        "getaround": ("getaround", "FF5F5F"),
        "zipcar": ("zipcar", "008731"),

        # Gas Stations
        "shell": ("shell", "FFD500"),
        "exxon": ("exxon", "ED2939"),
        "exxonmobil": ("exxonmobil", "ED2939"),
        "chevron": ("chevron", "D31245"),
        "bp": ("bp", "009E49"),
        "texaco": ("texaco", "CC0000"),
        "76": ("76", "E46C0A"),
        "sinclair": ("sinclairoil", "4AA25F"),
        "marathon": ("marathon", "1B2E4B"),
        "citgo": ("citgo", "D52B1E"),
        "sunoco": ("sunoco", "FECC00"),
        "valero": ("valero", "0033A0"),
        "phillips 66": ("phillips66", "F15A29"),
        "conoco": ("conoco", "CC0000"),
        "casey's": ("caseys", "E41F35"),
        "caseys": ("caseys", "E41F35"),
        "quiktrip": ("quiktrip", "CC0000"),
        "qt": ("quiktrip", "CC0000"),
        "wawa": ("wawa", "B1272C"),
        "sheetz": ("sheetz", "CC0000"),
        "racetrac": ("racetrac", "E61A22"),
        "loves": ("loves", "FFD100"),
        "pilot": ("pilotflyingj", "003058"),
        "flying j": ("pilotflyingj", "003058"),
        "speedway": ("speedway", "FABE00"),
        "7-eleven": ("7eleven", "146640"),
        "7eleven": ("7eleven", "146640"),
        "circle k": ("circlek", "ED1C24"),
        "cumberland farms": ("cumberlandfarms", "008C45"),
        "kum go": ("kumandgo", "E4002B"),
        "mapco": ("mapco", "00529B"),
        "maverick": ("maverick", "E31837"),
        "murphy usa": ("murphyusa", "CC0000"),
        "kwik trip": ("kwiktrip", "CE171E"),
        "kwik star": ("kwiktrip", "CE171E"),

        # Airlines
        "american airlines": ("americanairlines", "0078D2"),
        "delta": ("delta", "003366"),
        "united": ("unitedairlines", "002244"),
        "southwest": ("southwest", "304CB2"),
        "jetblue": ("jetblue", "003876"),
        "alaska airlines": ("alaskaairlines", "01426A"),
        "spirit": ("spiritairlines", "FFCD11"),
        "frontier": ("frontierairlines", "018643"),
        "hawaiian airlines": ("hawaiianairlines", "3E1651"),
        "allegiant": ("allegiant", "F68500"),
        "air canada": ("aircanada", "F01428"),
        "british airways": ("britishairways", "2E5C99"),
        "lufthansa": ("lufthansa", "05164D"),
        "emirates": ("emirates", "D71921"),
        "qatar": ("qatarairways", "5C0632"),
        "singapore airlines": ("singaporeairlines", "012A5C"),
        "cathay pacific": ("cathaypacific", "004145"),
        "ana": ("ana", "0074BC"),
        "japan airlines": ("japanairlines", "C8102E"),
        "korean air": ("koreanair", "0C4DA2"),
        "virgin atlantic": ("virginatlantic", "E10A0A"),
        "air france": ("airfrance", "002157"),
        "klm": ("klm", "00A1DE"),
        "turkish airlines": ("turkishairlines", "C70A0C"),
        "etihad": ("etihadairways", "BD8B13"),
        "eva air": ("evaair", "005F45"),
        "qantas": ("qantas", "F0001C"),

        # Travel & Hotels
        "airbnb": ("airbnb", "FF5A5F"),
        "vrbo": ("vrbo", "3661CE"),
        "booking": ("bookingdotcom", "003580"),
        "booking.com": ("bookingdotcom", "003580"),
        "expedia": ("expedia", "00355F"),
        "hotels.com": ("hotelsdotcom", "D32F2F"),
        "kayak": ("kayak", "FF690F"),
        "priceline": ("priceline", "1E5199"),
        "trivago": ("trivago", "007FAD"),
        "tripadvisor": ("tripadvisor", "34E0A1"),
        "marriott": ("marriott", "1C1C1C"),
        "hilton": ("hilton", "104C97"),
        "hyatt": ("hyatt", "D4AA00"),
        "ihg": ("ihg", "003A70"),
        "holiday inn": ("ihg", "003A70"),
        "crowne plaza": ("ihg", "003A70"),
        "wyndham": ("wyndham", "0074C0"),
        "la quinta": ("wyndham", "0074C0"),
        "ramada": ("wyndham", "0074C0"),
        "best western": ("bestwestern", "003B73"),
        "choice hotels": ("choicehotels", "0E438C"),
        "comfort inn": ("choicehotels", "0E438C"),
        "quality inn": ("choicehotels", "0E438C"),
        "radisson": ("radissonhotelgroup", "232C65"),
        "accor": ("accor", "26368B"),
        "four seasons": ("fourseasons", "1F1F1F"),
        "ritz carlton": ("ritzcarlton", "1F1F1F"),
        "westin": ("marriott", "1C1C1C"),
        "sheraton": ("marriott", "1C1C1C"),
        "w hotels": ("marriott", "1C1C1C"),
        "doubletree": ("hilton", "104C97"),
        "hampton inn": ("hilton", "104C97"),
        "embassy suites": ("hilton", "104C97"),
        "motel 6": ("motel6", "E21B23"),
        "super 8": ("wyndham", "0074C0"),

        # Streaming & Entertainment
        "netflix": ("netflix", "E50914"),
        "disney": ("disneyplus", "113CCF"),
        "disney+": ("disneyplus", "113CCF"),
        "disneyplus": ("disneyplus", "113CCF"),
        "hulu": ("hulu", "1CE783"),
        "hbo": ("hbo", "000000"),
        "hbo max": ("hbo", "000000"),
        "max": ("hbo", "000000"),
        "amazon prime": ("amazonprime", "00A8E1"),
        "prime video": ("primevideo", "00A8E1"),
        "apple tv": ("appletv", "000000"),
        "peacock": ("peacock", "000000"),
        "paramount": ("paramount", "0068CA"),
        "paramount+": ("paramountplus", "0068CA"),
        "discovery": ("discovery", "003087"),
        "discovery+": ("discoveryplus", "003087"),
        "youtube": ("youtube", "FF0000"),
        "youtube tv": ("youtubetv", "FF0000"),
        "youtube premium": ("youtube", "FF0000"),
        "spotify": ("spotify", "1DB954"),
        "apple music": ("applemusic", "FA243C"),
        "amazon music": ("amazonmusic", "FF9900"),
        "pandora": ("pandora", "3668FF"),
        "tidal": ("tidal", "000000"),
        "deezer": ("deezer", "FEAA2D"),
        "soundcloud": ("soundcloud", "FF5500"),
        "audible": ("audible", "F8991D"),
        "kindle": ("kindle", "FF9900"),
        "scribd": ("scribd", "1E7B85"),
        "xbox": ("xbox", "107C10"),
        "xbox game pass": ("xbox", "107C10"),
        "playstation": ("playstation", "003791"),
        "ps plus": ("playstation", "003791"),
        "nintendo": ("nintendo", "E60012"),
        "nintendo switch": ("nintendoswitch", "E60012"),
        "steam": ("steam", "000000"),
        "epic games": ("epicgames", "313131"),
        "twitch": ("twitch", "9146FF"),
        "discord": ("discord", "5865F2"),
        "crunchyroll": ("crunchyroll", "F47521"),
        "funimation": ("funimation", "5B0BB5"),
        "sling": ("sling", "0AA5FF"),
        "fubo": ("fubo", "C72127"),
        "philo": ("philo", "25D56C"),
        "mlb.tv": ("mlb", "002D72"),
        "nba": ("nba", "17408B"),
        "nfl": ("nfl", "013369"),
        "espn": ("espn", "D72428"),
        "espn+": ("espn", "D72428"),
        "amc": ("amc", "000000"),
        "starz": ("starz", "000000"),
        "showtime": ("showtime", "B10000"),
        "masterclass": ("masterclass", "282828"),
        "skillshare": ("skillshare", "00FF84"),
        "coursera": ("coursera", "0056D2"),
        "udemy": ("udemy", "A435F0"),
        "linkedin learning": ("linkedin", "0A66C2"),

        # Technology & Software
        "apple": ("apple", "000000"),
        "google": ("google", "4285F4"),
        "microsoft": ("microsoft", "5E5E5E"),
        "adobe": ("adobe", "FF0000"),
        "dropbox": ("dropbox", "0061FF"),
        "box": ("box", "0061D5"),
        "github": ("github", "181717"),
        "gitlab": ("gitlab", "FC6D26"),
        "bitbucket": ("bitbucket", "0052CC"),
        "atlassian": ("atlassian", "0052CC"),
        "jira": ("jira", "0052CC"),
        "confluence": ("confluence", "172B4D"),
        "trello": ("trello", "0052CC"),
        "asana": ("asana", "F06A6A"),
        "notion": ("notion", "000000"),
        "slack": ("slack", "4A154B"),
        "zoom": ("zoom", "2D8CFF"),
        "teams": ("microsoftteams", "6264A7"),
        "microsoft teams": ("microsoftteams", "6264A7"),
        "webex": ("webex", "000000"),
        "google meet": ("googlemeet", "00897B"),
        "1password": ("1password", "3B66BC"),
        "lastpass": ("lastpass", "D32D27"),
        "bitwarden": ("bitwarden", "175DDC"),
        "dashlane": ("dashlane", "0E353D"),
        "nordvpn": ("nordvpn", "4687FF"),
        "expressvpn": ("expressvpn", "DA3940"),
        "surfshark": ("surfshark", "178AE4"),
        "protonvpn": ("protonvpn", "66DEB1"),
        "norton": ("norton", "FFC000"),
        "mcafee": ("mcafee", "C01818"),
        "kaspersky": ("kaspersky", "006D5C"),
        "avast": ("avast", "FF7800"),
        "malwarebytes": ("malwarebytes", "0086C1"),
        "cloudflare": ("cloudflare", "F38020"),
        "aws": ("amazonwebservices", "232F3E"),
        "amazon web services": ("amazonwebservices", "232F3E"),
        "azure": ("microsoftazure", "0078D4"),
        "google cloud": ("googlecloud", "4285F4"),
        "digitalocean": ("digitalocean", "0080FF"),
        "heroku": ("heroku", "430098"),
        "vercel": ("vercel", "000000"),
        "netlify": ("netlify", "00C7B7"),
        "godaddy": ("godaddy", "1BDBDB"),
        "namecheap": ("namecheap", "DE3723"),
        "squarespace": ("squarespace", "000000"),
        "wix": ("wix", "0C6EFC"),
        "wordpress": ("wordpress", "21759B"),
        "shopify": ("shopify", "7AB55C"),
        "mailchimp": ("mailchimp", "FFE01B"),
        "constant contact": ("constantcontact", "004BA0"),
        "hubspot": ("hubspot", "FF7A59"),
        "salesforce": ("salesforce", "00A1E0"),
        "quickbooks": ("quickbooks", "2CA01C"),
        "intuit": ("intuit", "236EB9"),
        "freshbooks": ("freshbooks", "0075DD"),
        "xero": ("xero", "13B5EA"),
        "wave": ("wave", "003CB4"),
        "stripe": ("stripe", "008CDD"),
        "square": ("square", "3E4348"),
        "paypal": ("paypal", "003087"),
        "venmo": ("venmo", "008CFF"),
        "zelle": ("zelle", "6D1ED4"),
        "cash app": ("cashapp", "00D632"),
        "cashapp": ("cashapp", "00D632"),
        "wise": ("wise", "00B9FF"),
        "transferwise": ("wise", "00B9FF"),
        "coinbase": ("coinbase", "0052FF"),
        "robinhood": ("robinhood", "00C805"),
        "fidelity": ("fidelity", "208D28"),
        "vanguard": ("vanguard", "96151D"),
        "schwab": ("charlesschwab", "00A3E0"),
        "charles schwab": ("charlesschwab", "00A3E0"),
        "etrade": ("etrade", "6633CC"),
        "td ameritrade": ("tdameritrade", "3CBB00"),
        "acorns": ("acorns", "54B948"),
        "stash": ("stash", "4D2177"),
        "wealthfront": ("wealthfront", "00B9F1"),
        "betterment": ("betterment", "1F2633"),
        "sofi": ("sofi", "73CDDD"),
        "chime": ("chime", "01C585"),
        "ally": ("ally", "5C068C"),
        "capital one": ("capitalone", "CC0000"),
        "chase": ("chase", "117ACA"),
        "bank of america": ("bankofamerica", "012169"),
        "wells fargo": ("wellsfargo", "CD1409"),
        "citi": ("citibank", "003DA5"),
        "citibank": ("citibank", "003DA5"),
        "us bank": ("usbank", "0D3768"),
        "pnc": ("pnc", "F58025"),
        "td bank": ("td", "34A853"),
        "truist": ("truist", "8313A2"),
        "regions": ("regions", "008540"),
        "fifth third": ("fifththirdbank", "015E32"),
        "huntington": ("huntington", "00A94F"),
        "key bank": ("keybank", "4B7F52"),
        "discover": ("discover", "FF6600"),
        "american express": ("americanexpress", "006FCF"),
        "amex": ("americanexpress", "006FCF"),
        "mastercard": ("mastercard", "EB001B"),
        "visa": ("visa", "1A1F71"),

        # Telecommunications
        "verizon": ("verizon", "CD040B"),
        "at&t": ("att", "009FDB"),
        "att": ("att", "009FDB"),
        "t-mobile": ("tmobile", "E20074"),
        "tmobile": ("tmobile", "E20074"),
        "sprint": ("sprint", "FFCE00"),
        "xfinity": ("xfinity", "E30000"),
        "comcast": ("xfinity", "E30000"),
        "spectrum": ("spectrum", "0077C8"),
        "cox": ("cox", "F46A25"),
        "frontier": ("frontier", "FF0037"),
        "centurylink": ("centurylink", "00B388"),
        "lumen": ("centurylink", "00B388"),
        "optimum": ("altice", "FF1617"),
        "google fi": ("googlefi", "4285F4"),
        "mint mobile": ("mintmobile", "53A83B"),
        "visible": ("visible", "003ACF"),
        "cricket": ("cricket", "72B844"),
        "boost mobile": ("boostmobile", "F36F21"),
        "metro": ("metro", "E20074"),
        "us cellular": ("uscellular", "003865"),
        "straight talk": ("straighttalk", "EC7F1A"),
        "tracfone": ("tracfone", "E31837"),

        # Insurance
        "geico": ("geico", "013769"),
        "progressive": ("progressive", "0055A4"),
        "state farm": ("statefarm", "CE1126"),
        "allstate": ("allstate", "0066CC"),
        "liberty mutual": ("libertymutual", "E8BA00"),
        "farmers": ("farmers", "003B5C"),
        "nationwide": ("nationwide", "003366"),
        "usaa": ("usaa", "1A3B69"),
        "travelers": ("travelers", "CC0000"),
        "aetna": ("aetna", "7D3F98"),
        "cigna": ("cigna", "ED8B00"),
        "united healthcare": ("unitedhealthcare", "002677"),
        "blue cross": ("bluecrossbluestate", "003087"),
        "bcbs": ("bluecrossbluestate", "003087"),
        "anthem": ("anthem", "003768"),
        "humana": ("humana", "33A02C"),
        "kaiser": ("kaiserpermanente", "003B71"),
        "metlife": ("metlife", "00923F"),
        "prudential": ("prudential", "005587"),
        "aflac": ("aflac", "00A3E0"),
        "lemonade": ("lemonade", "FF0083"),

        # Fitness & Health
        "peloton": ("peloton", "000000"),
        "planet fitness": ("planetfitness", "5A2D82"),
        "la fitness": ("lafitness", "E31837"),
        "equinox": ("equinox", "000000"),
        "orangetheory": ("orangetheory", "F36F21"),
        "crossfit": ("crossfit", "C41F24"),
        "24 hour fitness": ("24hourfitness", "EE3124"),
        "anytime fitness": ("anytimefitness", "6A408D"),
        "gold's gym": ("goldsgym", "C6A664"),
        "lifetime fitness": ("lifetime", "00D100"),
        "ymca": ("ymca", "003087"),
        "nike training": ("nike", "000000"),
        "fitbit": ("fitbit", "00B0B9"),
        "garmin": ("garmin", "000000"),
        "strava": ("strava", "FC4C02"),
        "myfitnesspal": ("myfitnesspal", "0066CC"),
        "noom": ("noom", "00B5AA"),
        "weight watchers": ("ww", "0095D9"),
        "ww": ("ww", "0095D9"),
        "headspace": ("headspace", "F47D31"),
        "calm": ("calm", "5ACEE9"),
        "betterhelp": ("betterhelp", "2E6E4E"),
        "talkspace": ("talkspace", "17B890"),
        "zocdoc": ("zocdoc", "50B6C2"),
        "goodrx": ("goodrx", "FFE702"),
        "cvs pharmacy": ("cvs", "CC0000"),
        "rite aid": ("riteaid", "003DA5"),

        # Utilities
        "electric": ("lightning", "F7DF1E"),
        "power": ("lightning", "F7DF1E"),
        "gas utility": ("flame", "FF6600"),
        "water": ("droplet", "0096FF"),
        "sewer": ("droplet", "0096FF"),
        "trash": ("recycle", "00B336"),
        "garbage": ("recycle", "00B336"),
        "waste management": ("wastemanagement", "00A84F"),
        "republic services": ("republicservices", "003468"),
        "adt": ("adt", "0065AB"),
        "vivint": ("vivint", "0056B8"),
        "simplisafe": ("simplisafe", "112D4E"),
        "ring": ("ring", "1C9AD6"),
        "nest": ("googlenest", "4285F4"),

        # Social Media
        "facebook": ("facebook", "1877F2"),
        "instagram": ("instagram", "E4405F"),
        "twitter": ("x", "000000"),
        "x": ("x", "000000"),
        "linkedin": ("linkedin", "0A66C2"),
        "tiktok": ("tiktok", "000000"),
        "snapchat": ("snapchat", "FFFC00"),
        "pinterest": ("pinterest", "E60023"),
        "reddit": ("reddit", "FF4500"),
        "tumblr": ("tumblr", "36465D"),
        "whatsapp": ("whatsapp", "25D366"),
        "telegram": ("telegram", "26A5E4"),
        "signal": ("signal", "3A76F0"),
        "wechat": ("wechat", "07C160"),
        "line": ("line", "00C300"),
        "skype": ("skype", "00AFF0"),
        "viber": ("viber", "665CAC"),
        "meetup": ("meetup", "ED1C40"),
        "bumble": ("bumble", "FFFC00"),
        "tinder": ("tinder", "FF6B6B"),
        "hinge": ("hinge", "FFBDB9"),
        "match": ("match", "FF6F61"),
        "okcupid": ("okcupid", "0500FF"),
        "patreon": ("patreon", "FF424D"),
        "onlyfans": ("onlyfans", "00AFF0"),
        "ko-fi": ("kofi", "FF5E5B"),
        "buymeacoffee": ("buymeacoffee", "FFDD00"),

        # Education
        "chegg": ("chegg", "F27128"),
        "quizlet": ("quizlet", "4255FF"),
        "duolingo": ("duolingo", "58CC02"),
        "rosetta stone": ("rosettastone", "253B80"),
        "babbel": ("babbel", "F0502F"),
        "khan academy": ("khanacademy", "14BF96"),
        "brilliant": ("brilliant", "000000"),
        "codecademy": ("codecademy", "1F4056"),
        "pluralsight": ("pluralsight", "F15B2A"),
        "treehouse": ("treehouse", "5FCF80"),
        "datacamp": ("datacamp", "03EF62"),
        "grammarly": ("grammarly", "15C39A"),

        # News & Media
        "new york times": ("newyorktimes", "000000"),
        "nytimes": ("newyorktimes", "000000"),
        "washington post": ("washingtonpost", "000000"),
        "wall street journal": ("wsj", "000000"),
        "wsj": ("wsj", "000000"),
        "cnn": ("cnn", "CC0000"),
        "fox news": ("foxnews", "003366"),
        "msnbc": ("msnbc", "0A7BBF"),
        "bbc": ("bbc", "000000"),
        "npr": ("npr", "EC1E24"),
        "the atlantic": ("theatlantic", "000000"),
        "the guardian": ("theguardian", "052962"),
        "economist": ("theeconomist", "E3120B"),
        "bloomberg": ("bloomberg", "2800D7"),
        "reuters": ("reuters", "FF8000"),
        "associated press": ("associatedpress", "FF322E"),
        "usa today": ("usatoday", "009BFF"),
        "medium": ("medium", "000000"),
        "substack": ("substack", "FF6719"),
        "pocket": ("pocket", "EF4056"),
        "feedly": ("feedly", "2BB24C"),
        "flipboard": ("flipboard", "E12828"),
    }

    # Emoji mappings by category/keyword
    # Format: "keyword": "emoji"
    EMOJI_MAPPINGS: Dict[str, str] = {
        # Food & Dining
        "restaurant": "🍽️",
        "food": "🍴",
        "dining": "🍽️",
        "cafe": "☕",
        "coffee": "☕",
        "bakery": "🥐",
        "pizza": "🍕",
        "burger": "🍔",
        "sushi": "🍣",
        "chinese": "🥡",
        "thai": "🍜",
        "vietnamese": "🍜",
        "pho": "🍜",
        "ramen": "🍜",
        "noodle": "🍜",
        "mexican": "🌮",
        "taco": "🌮",
        "burrito": "🌯",
        "italian": "🍝",
        "pasta": "🍝",
        "indian": "🍛",
        "curry": "🍛",
        "bbq": "🍖",
        "barbecue": "🍖",
        "grill": "🍖",
        "steakhouse": "🥩",
        "steak": "🥩",
        "seafood": "🦐",
        "fish": "🐟",
        "wings": "🍗",
        "chicken": "🍗",
        "sandwich": "🥪",
        "sub": "🥪",
        "deli": "🥪",
        "salad": "🥗",
        "healthy": "🥗",
        "vegan": "🥬",
        "vegetarian": "🥬",
        "breakfast": "🍳",
        "brunch": "🍳",
        "pancake": "🥞",
        "waffle": "🧇",
        "donut": "🍩",
        "doughnut": "🍩",
        "ice cream": "🍦",
        "frozen yogurt": "🍦",
        "dessert": "🍰",
        "cake": "🎂",
        "candy": "🍬",
        "chocolate": "🍫",
        "smoothie": "🥤",
        "juice": "🧃",
        "boba": "🧋",
        "tea": "🍵",
        "bar": "🍺",
        "pub": "🍺",
        "brewery": "🍺",
        "beer": "🍺",
        "wine": "🍷",
        "winery": "🍷",
        "liquor": "🥃",
        "spirits": "🥃",
        "cocktail": "🍸",

        # Shopping & Retail
        "grocery": "🛒",
        "supermarket": "🛒",
        "market": "🛒",
        "store": "🏪",
        "shop": "🛍️",
        "shopping": "🛍️",
        "mall": "🏬",
        "department": "🏬",
        "outlet": "🏷️",
        "discount": "🏷️",
        "thrift": "👕",
        "consignment": "👗",
        "clothing": "👔",
        "apparel": "👕",
        "fashion": "👗",
        "shoes": "👟",
        "footwear": "👞",
        "jewelry": "💎",
        "watch": "⌚",
        "accessories": "👜",
        "handbag": "👜",
        "purse": "👛",
        "cosmetics": "💄",
        "beauty": "💅",
        "skincare": "🧴",
        "salon": "💇",
        "spa": "🧖",
        "barber": "💈",
        "hair": "💇",
        "nail": "💅",
        "furniture": "🛋️",
        "home": "🏠",
        "decor": "🖼️",
        "garden": "🌻",
        "plant": "🌱",
        "nursery": "🌳",
        "hardware": "🔧",
        "tools": "🛠️",
        "craft": "🎨",
        "art": "🎨",
        "hobby": "🎯",
        "toy": "🧸",
        "game": "🎮",
        "book": "📚",
        "bookstore": "📖",
        "music": "🎵",
        "record": "💿",
        "electronics": "📱",
        "computer": "💻",
        "tech": "🖥️",
        "phone": "📱",
        "appliance": "🔌",
        "office": "🗄️",
        "supplies": "📎",
        "stationery": "✏️",
        "pet": "🐾",
        "pet store": "🐕",
        "vet": "🏥",
        "veterinary": "🐈",
        "pharmacy": "💊",
        "drugstore": "💊",
        "optical": "👓",
        "glasses": "👓",
        "eyewear": "🕶️",

        # Transportation
        "gas": "⛽",
        "fuel": "⛽",
        "gasoline": "⛽",
        "petrol": "⛽",
        "auto": "🚗",
        "car": "🚗",
        "vehicle": "🚙",
        "automotive": "🚘",
        "parking": "🅿️",
        "toll": "🛣️",
        "highway": "🛣️",
        "taxi": "🚕",
        "cab": "🚕",
        "rideshare": "🚗",
        "ride": "🚗",
        "transit": "🚌",
        "bus": "🚌",
        "train": "🚆",
        "rail": "🚃",
        "metro": "🚇",
        "subway": "🚇",
        "ferry": "⛴️",
        "boat": "🚤",
        "ship": "🚢",
        "cruise": "🛳️",
        "airline": "✈️",
        "flight": "✈️",
        "airport": "🛫",
        "travel": "🧳",
        "vacation": "🏖️",
        "hotel": "🏨",
        "motel": "🏨",
        "lodging": "🛏️",
        "resort": "🏝️",
        "rental": "🔑",
        "car rental": "🚗",
        "bike": "🚲",
        "bicycle": "🚲",
        "scooter": "🛴",
        "motorcycle": "🏍️",
        "repair": "🔧",
        "mechanic": "👨‍🔧",
        "tire": "🛞",
        "oil change": "🛢️",
        "carwash": "🚿",
        "car wash": "🚿",
        "detailing": "✨",

        # Services & Utilities
        "electric": "⚡",
        "electricity": "⚡",
        "power": "⚡",
        "water": "💧",
        "sewer": "💧",
        "gas utility": "🔥",
        "heat": "🔥",
        "heating": "🔥",
        "cooling": "❄️",
        "hvac": "🌡️",
        "internet": "🌐",
        "wifi": "📶",
        "cable": "📺",
        "tv": "📺",
        "television": "📺",
        "phone": "📱",
        "mobile": "📱",
        "cellular": "📶",
        "wireless": "📡",
        "telecom": "📞",
        "trash": "🗑️",
        "garbage": "🗑️",
        "waste": "♻️",
        "recycling": "♻️",
        "cleaning": "🧹",
        "housekeeping": "🧹",
        "maid": "🧹",
        "laundry": "🧺",
        "dry cleaning": "👔",
        "landscaping": "🌿",
        "lawn": "🌾",
        "pool": "🏊",
        "pest control": "🐜",
        "exterminator": "🐛",
        "security": "🔒",
        "alarm": "🚨",
        "locksmith": "🔑",
        "plumber": "🔧",
        "plumbing": "🚿",
        "electrician": "⚡",
        "contractor": "👷",
        "construction": "🏗️",
        "renovation": "🔨",
        "remodel": "🏠",
        "moving": "📦",
        "storage": "📦",
        "shipping": "📬",
        "delivery": "📦",
        "mail": "📮",
        "postal": "📯",
        "courier": "📨",

        # Finance & Business
        "bank": "🏦",
        "banking": "🏦",
        "atm": "🏧",
        "credit": "💳",
        "debit": "💳",
        "loan": "💰",
        "mortgage": "🏠",
        "insurance": "🛡️",
        "investment": "📈",
        "stock": "📊",
        "trading": "📉",
        "crypto": "₿",
        "bitcoin": "₿",
        "tax": "📋",
        "accounting": "🧮",
        "legal": "⚖️",
        "lawyer": "👨‍⚖️",
        "attorney": "👩‍⚖️",
        "notary": "📝",
        "consulting": "💼",
        "professional": "👔",
        "business": "🏢",
        "corporate": "🏛️",
        "government": "🏛️",
        "municipal": "🏛️",
        "city": "🏙️",
        "county": "🏛️",
        "state": "🏛️",
        "federal": "🏛️",
        "fees": "💵",
        "dues": "💵",
        "membership": "🎫",
        "subscription": "📆",
        "license": "📄",
        "registration": "📝",
        "permit": "📋",

        # Health & Medical
        "doctor": "👨‍⚕️",
        "physician": "👩‍⚕️",
        "medical": "🏥",
        "hospital": "🏥",
        "clinic": "🏥",
        "urgent care": "🚑",
        "emergency": "🚨",
        "dental": "🦷",
        "dentist": "🦷",
        "orthodontist": "🦷",
        "vision": "👁️",
        "eye": "👁️",
        "optometrist": "👓",
        "mental health": "🧠",
        "therapy": "💆",
        "counseling": "🗣️",
        "psychiatry": "🧠",
        "psychology": "🧠",
        "chiropractor": "🦴",
        "physical therapy": "💪",
        "pt": "💪",
        "massage": "💆",
        "acupuncture": "📍",
        "lab": "🔬",
        "laboratory": "🧪",
        "imaging": "🩻",
        "xray": "🩻",
        "mri": "🩻",
        "surgery": "🏥",
        "specialist": "👨‍⚕️",
        "dermatology": "🧴",
        "cardiology": "❤️",
        "pediatric": "👶",
        "obgyn": "🤰",
        "prenatal": "🤰",
        "wellness": "🌿",
        "fitness": "💪",
        "gym": "🏋️",
        "workout": "🏋️",
        "yoga": "🧘",
        "pilates": "🧘",
        "martial arts": "🥋",
        "sports": "⚽",
        "athletic": "🏃",
        "nutrition": "🥗",
        "vitamins": "💊",
        "supplements": "💊",

        # Entertainment & Recreation
        "movie": "🎬",
        "cinema": "🎬",
        "theater": "🎭",
        "theatre": "🎭",
        "concert": "🎤",
        "music": "🎵",
        "show": "🎪",
        "event": "🎟️",
        "ticket": "🎫",
        "museum": "🏛️",
        "gallery": "🖼️",
        "zoo": "🦁",
        "aquarium": "🐠",
        "park": "🌳",
        "theme park": "🎢",
        "amusement": "🎡",
        "arcade": "🕹️",
        "bowling": "🎳",
        "golf": "⛳",
        "tennis": "🎾",
        "swimming": "🏊",
        "skiing": "⛷️",
        "snowboard": "🏂",
        "beach": "🏖️",
        "camping": "🏕️",
        "hiking": "🥾",
        "fishing": "🎣",
        "hunting": "🦌",
        "outdoor": "🏔️",
        "adventure": "🧗",
        "club": "🎉",
        "nightclub": "🪩",
        "casino": "🎰",
        "gambling": "🎲",
        "lottery": "🎟️",
        "spa": "💆",
        "massage": "💆",
        "streaming": "📺",
        "gaming": "🎮",
        "video game": "🎮",
        "esports": "🎮",

        # Education & Kids
        "school": "🏫",
        "education": "📚",
        "university": "🎓",
        "college": "🎓",
        "tuition": "📚",
        "course": "📖",
        "class": "📝",
        "tutoring": "👨‍🏫",
        "lesson": "📖",
        "music lesson": "🎹",
        "dance": "💃",
        "daycare": "👶",
        "childcare": "👶",
        "preschool": "🎒",
        "camp": "🏕️",
        "afterschool": "🎒",
        "extracurricular": "🎯",
        "sports": "⚽",
        "activity": "🎯",
        "birthday": "🎂",
        "party": "🎉",
        "celebration": "🎊",

        # Home & Living
        "rent": "🏠",
        "mortgage": "🏡",
        "housing": "🏘️",
        "apartment": "🏢",
        "condo": "🏢",
        "real estate": "🏠",
        "property": "🏠",
        "hoa": "🏘️",
        "maintenance": "🔧",
        "repair": "🔧",
        "improvement": "🏠",
        "furniture": "🛋️",
        "appliance": "🔌",
        "decoration": "🖼️",
        "interior": "🏠",

        # Personal Care
        "grooming": "💈",
        "haircut": "💇",
        "beauty": "💄",
        "cosmetic": "💅",
        "personal": "🧴",
        "hygiene": "🧼",

        # Gifts & Charity
        "gift": "🎁",
        "present": "🎁",
        "donation": "❤️",
        "charity": "🤝",
        "nonprofit": "❤️",
        "church": "⛪",
        "religious": "🙏",
        "tithe": "🙏",
        "offering": "🙏",

        # Miscellaneous
        "general": "🏪",
        "misc": "📌",
        "other": "📌",
        "unknown": "❓",
        "atm": "🏧",
        "cash": "💵",
        "withdrawal": "💵",
        "transfer": "💸",
        "payment": "💳",
        "fee": "💵",
        "interest": "📈",
        "refund": "💰",
        "rebate": "💰",
        "reward": "🏆",
        "cashback": "💵",
    }

    # Default emoji when no match is found
    DEFAULT_EMOJI = "🏪"

    def __init__(self):
        """Initialize the PayeeIconService."""
        # Pre-compile name normalization patterns
        self._normalize_pattern = re.compile(r'[^a-z0-9\s]')
        self._whitespace_pattern = re.compile(r'\s+')

    def _normalize_name(self, name: str) -> str:
        """Normalize a payee name for matching."""
        # Lowercase and remove special characters
        normalized = self._normalize_pattern.sub('', name.lower())
        # Collapse whitespace
        normalized = self._whitespace_pattern.sub(' ', normalized).strip()
        return normalized

    def _find_best_brand_match(self, name: str) -> Optional[Tuple[str, str, str]]:
        """
        Find the best matching brand for a payee name.

        Returns tuple of (slug, hex_color, matched_brand) or None if no match.
        """
        normalized = self._normalize_name(name)

        # First, try exact match
        if normalized in self.BRAND_MAPPINGS:
            slug, color = self.BRAND_MAPPINGS[normalized]
            return (slug, color, normalized)

        # Try partial matches - check if any brand is contained in the name
        best_match = None
        best_length = 0

        for brand, (slug, color) in self.BRAND_MAPPINGS.items():
            if brand in normalized:
                # Prefer longer matches (more specific)
                if len(brand) > best_length:
                    best_match = (slug, color, brand)
                    best_length = len(brand)

        if best_match:
            return best_match

        # Try fuzzy matching for close matches
        for brand, (slug, color) in self.BRAND_MAPPINGS.items():
            similarity = SequenceMatcher(None, normalized, brand).ratio()
            if similarity > 0.85:  # High threshold for brand matching
                return (slug, color, brand)

        return None

    def _find_best_emoji(self, name: str) -> Tuple[str, Optional[str]]:
        """
        Find the best matching emoji for a payee name.

        Returns tuple of (emoji, matched_keyword) or (default_emoji, None).
        """
        normalized = self._normalize_name(name)
        words = set(normalized.split())

        # Check for keyword matches
        best_match = None
        best_length = 0

        for keyword, emoji in self.EMOJI_MAPPINGS.items():
            keyword_words = set(keyword.split())

            # Check if all keyword words are in the name
            if keyword_words.issubset(words):
                if len(keyword) > best_length:
                    best_match = (emoji, keyword)
                    best_length = len(keyword)
            # Also check if keyword is a substring
            elif keyword in normalized:
                if len(keyword) > best_length:
                    best_match = (emoji, keyword)
                    best_length = len(keyword)

        if best_match:
            return best_match

        # Check individual words
        for word in words:
            if word in self.EMOJI_MAPPINGS:
                return (self.EMOJI_MAPPINGS[word], word)

        return (self.DEFAULT_EMOJI, None)

    def suggest_icon(self, payee_name: str) -> dict:
        """
        Suggest an icon (brand logo or emoji) for a payee.

        Returns a dict with:
        - icon_type: "brand" or "emoji"
        - icon_value: CDN URL for brand, emoji character for emoji
        - brand_color: hex color if brand, None otherwise
        - matched_term: what was matched
        - confidence: match confidence (1.0 for exact, lower for fuzzy)

        The icon_value can be stored directly in the payee's logo_url field.
        For emojis, the format is "emoji:{emoji_char}" (e.g., "emoji:☕")
        For brands, it's the full CDN URL.
        """
        # Try to find a brand match first
        brand_match = self._find_best_brand_match(payee_name)

        if brand_match:
            slug, color, matched = brand_match
            # Calculate confidence based on match type
            normalized = self._normalize_name(payee_name)
            if normalized == matched:
                confidence = 1.0
            elif matched in normalized:
                # Partial match - confidence based on how much of name is the brand
                confidence = len(matched) / len(normalized)
            else:
                # Fuzzy match
                confidence = SequenceMatcher(None, normalized, matched).ratio()

            return {
                "icon_type": "brand",
                "icon_value": f"{self.SIMPLE_ICONS_CDN}/{slug}/{color}",
                "brand_color": f"#{color}",
                "matched_term": matched,
                "confidence": round(confidence, 2),
                "slug": slug,
            }

        # Fall back to emoji
        emoji, matched = self._find_best_emoji(payee_name)
        confidence = 0.8 if matched else 0.3  # Lower confidence for default emoji

        return {
            "icon_type": "emoji",
            "icon_value": f"emoji:{emoji}",
            "brand_color": None,
            "matched_term": matched,
            "confidence": round(confidence, 2),
            "emoji": emoji,
        }

    def get_brand_url(self, slug: str, color: Optional[str] = None) -> str:
        """Get the CDN URL for a brand icon by slug."""
        if color:
            return f"{self.SIMPLE_ICONS_CDN}/{slug}/{color}"
        return f"{self.SIMPLE_ICONS_CDN}/{slug}"

    def parse_logo_url(self, logo_url: Optional[str]) -> dict:
        """
        Parse a stored logo_url into its components.

        Returns dict with:
        - type: "brand", "emoji", "custom", or "none"
        - value: the emoji character, brand URL, or custom URL
        - display_value: what to show in UI (emoji char or img src)
        """
        if not logo_url:
            return {
                "type": "none",
                "value": None,
                "display_value": self.DEFAULT_EMOJI,
            }

        if logo_url.startswith("emoji:"):
            emoji = logo_url[6:]  # Remove "emoji:" prefix
            return {
                "type": "emoji",
                "value": emoji,
                "display_value": emoji,
            }

        if self.SIMPLE_ICONS_CDN in logo_url:
            return {
                "type": "brand",
                "value": logo_url,
                "display_value": logo_url,
            }

        # Assume it's a custom URL
        return {
            "type": "custom",
            "value": logo_url,
            "display_value": logo_url,
        }

    def get_all_brands(self) -> list:
        """Get list of all available brand mappings for documentation."""
        brands = []
        seen_slugs = set()

        for name, (slug, color) in sorted(self.BRAND_MAPPINGS.items()):
            if slug not in seen_slugs:
                brands.append({
                    "name": name.title(),
                    "slug": slug,
                    "color": f"#{color}",
                    "url": f"{self.SIMPLE_ICONS_CDN}/{slug}/{color}",
                })
                seen_slugs.add(slug)

        return brands

    def get_emoji_categories(self) -> dict:
        """Get emoji mappings organized by category for documentation."""
        # Group emojis by their emoji character
        by_emoji = {}
        for keyword, emoji in self.EMOJI_MAPPINGS.items():
            if emoji not in by_emoji:
                by_emoji[emoji] = []
            by_emoji[emoji].append(keyword)

        return by_emoji


# Singleton instance for easy import
payee_icon_service = PayeeIconService()
