import re
import unicodedata

# --- helpers ---
def _norm(s: str) -> str:
    s = (s or "").lower()
    # strip accents and normalize spaces
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _has(pat: str, text: str) -> bool:
    return re.search(pat, text, flags=re.I) is not None


# ---------- KEYWORDS ----------
# Base protein/ingredient → station (used as fallback after higher-priority rules)
KEYWORDS = {
    "cumi telor bakar": "bakaran",
    "cumi saus padang": "masak",
    "cumi saus tiram": "masak",
    "tauge tahu": "sayuran",
    "udang goreng mentega": "cumi",
    "brokoli": "sayuran",
    "krapu sambal game": "bakaran",
    "pete balado": "masak",
    "pete bakar": "masak",
    "pete gk": "masak",
    "pete rebus": "masak",
    "tahu krispi": "cumi",
    "goreng mentega": "steam",
    "goreng kipas": "steam",
    "lalapan": "masak",
    "nasi goreng ayam": "masak",
    "mie goreng ayam": "masak",
    "tahu tempe mix": "cumi",
    "genjer": "sayuran",
    "tahu telur asin": "cumi",
    "tempe goreng": "cumi",
    "tahu goreng": "cumi",

    # FILET → cumi line
    "gurame fillet": "cumi",
    "kakap fillet": "cumi",
    "krapu fillet": "cumi",

    # VEGETABLES → sayuran
    "toge tahu": "sayuran",
    "tumis genjer tanpa udang": "sayuran",
    "toge udang": "sayuran",

    # Starches
    "nasi goreng": "masak",
    "bihun": "masak",

    # FISH “saus/saus …” default to STEAM for those species
    "gurame saus": "steam",
    "baronang saus": "steam",
    "bawal hitam saus": "steam",
    "bawal bintang saus": "steam",
    "kuwe saus": "steam",
    "krapu saus": "steam",
    "kakap saus": "steam",

    # Cumi styles (masak station)
    "cumi saus padang": "masak",
    "cumi asam manis": "masak",
    "cumi goreng mentega": "masak",
    "cumi tauco": "masak",
    "cumi saus tiram": "masak",
    "cumi lada hitam": "masak",
    "cumi tinta hitam": "masak",
    "cumi cabe hijau": "masak",

    # BASE PROTEINS
    "cumi": "cumi",          # base: wok line
    "udang": "cumi",         # udang shares the wok line (will be overridden by priority rules below when needed)
    "kerang": "steam",
    "api masak": "steam",

    # Kepiting
    "kepiting": "bakaran",   # generic kepiting → bakaran, kepiting soka handled in priority rules

    # udang api masak special → STEAM (important)
    "udang api masak": "steam",

    # other
    "tahu gandum": "cumi",
    "ayam": "steam",

    # techniques / styles
    "steam":  "steam",
    "hongkong": "steam",
    "nyonya": "steam",
    "garden": "steam",
    "tahu": "masak",
    "bakar spesial": "masak",
    "bakar":  "bakaran",
    "panggang": "bakaran",
    "goreng kipas": "steam",
    "goreng kering": "steam",     # fish-specific override handled by PRIORITY_RULES
    "cumi goreng mentega": "masak",
    "asam manis": "steam",
    "asam pedas": "steam",
    "lada hitam": "masak",
    "saus padang": "steam",
    "saus padang": "steam",
    "saus tiram": "steam",
    "tauco": "steam",
    "sop": "steam",
    "rebus": "steam",
    "mie": "masak",

    # drinks
    "teh": "bar",
    "kopi": "bar",
    "soda": "bar",
    "sirup": "bar",
}


# ---------- CATEGORY DEFAULTS ----------
CATEGORY_DEFAULTS = {
    "Minuman": "bar",
    "Nasi": "masak",
    "Sayur": "sayuran",
    "Lain Lain": "masak",
    "Kuah Masak": "masak",
    "Ikan": "masak",
    "Cumi": "cumi",
    "Udang": "cumi",
    "Kerang Bambu": "steam",
    "Kerang Kepa": "steam",
    "Kerang Ijo": "steam",
    "Kerang Dara": "steam",
    "Keong Macan": "steam",
    "Kepiting": "bakaran",
    "Kepiting Jantan": "bakaran",
    "Kepiting Telor": "bakaran",
    "Kepiting Soka": "cumi",
    "Ekstra Telor": "masak",
    "Ayam": "steam",  
}

# ---------- HARD / PRIORITY RULES ----------
# Order matters: first match wins.
PRIORITY_RULES = [
    # 1) Absolute category locks: all Kerang*/Keong → STEAM
    (lambda name, cats: cats[:1] and cats[0] in {
        "Kerang Bambu", "Kerang Kepa", "Kerang Ijo", "Kerang Dara", "Keong Macan"
    }, "steam"),

    # 2) Kepiting routing
    (lambda name, cats: "kepiting soka" in name, "cumi"),  # Soka → cumi
    (lambda name, cats: ("kepiting" in name) or (cats[:1] and cats[0].startswith("Kepiting")), "bakaran"),

    # 3) FILET fish → CUMI station (any fillet)
    (lambda name, cats: _has(r"\bfilet\b|\bfillet\b", name), "cumi"),

    # 4) Sapo tahu → masak
    (lambda name, cats: "sapo tahu" in name, "masak"),

    # 4b) Cumi goreng mentega must stay on masak (override generic goreng-mentega → steam)
    (lambda name, cats: "cumi goreng mentega" in name, "masak"),

    # 5) Roti Mantau → cumi
    (lambda name, cats: _has(r"\b(roti )?mantau\b|\bmantao\b", name), "cumi"),

    # 6) Fish (category "Ikan") styles that must be STEAM
    #    covers Gurame/Baronang/Bawal/Bawal Bintang/Kuwe/Krapu variants you listed
    (
        lambda name, cats: (
            cats[:1] and cats[0] == "Ikan"
            and not _has(r"\bfilet\b|\bfillet\b", name)  # fillet handled above (goes to cumi)
            and (
                _has(r"\bgoreng kering\b", name) or
                _has(r"\bsambal game\b", name) or
                _has(r"\basam manis\b", name) or
                _has(r"\bgoreng mentega\b", name) or
                _has(r"\bspesial tauc?o\b", name) or
                _has(r"\btauc?o\b", name) or
                _has(r"\b(lada hitam|ldh)\b", name) or
                _has(r"\bsingapore\b", name) or
                _has(r"\bsop\b", name) or             # sop bening / sop kuning biasa / sop kuning asam
                _has(r"\basam pedas\b", name) or
                _has(r"\bsaus padang\b", name) or     # "sp"
                _has(r"\bsaus padang\b", name) or
                _has(r"\bsaus tiram\b", name) or      # "st"
                _has(r"\bsaus tiram\b", name)
            )
        ),
        "steam",
    ),

    # 7) Generic fish “goreng ...” → STEAM (non-fillet only), as backup
    (
        lambda name, cats: (
            cats[:1] and cats[0] == "Ikan"
            and not _has(r"\bfilet\b|\bfillet\b", name)
            and _has(r"\bgor(e|)wng\b|\bgoreng\b", name)
        ),
        "steam",
    ),

    # 8) Udang rebus / masak / GK that must be STEAM
    (
        lambda name, cats: _has(
            r"\budang pancet\b.*\brebus\b|"   # Udang Pancet Rebus
            r"\budang jumbo\b.*\brebus\b|"    # Udang Jumbo Rebus
            r"\budang api\b.*\brebus\b|"      # Udang Api Rebus
            r"\budang api\b.*\bmasak\b|"      # Udang Api Masak
            r"\budang api\b.*\bgk\b",         # Udang Api GK
            name
        ),
        "steam",
    ),

    # 9) Udang Balado → STEAM (but only udang, not generic balado)
    (
        lambda name, cats: _has(r"\budang\b.*\bbalado\b", name),
        "steam",
    ),

    # 10) Technique beats protein (generic)
    # NOTE: do NOT send Pete Bakar to bakaran – let KEYWORDS handle all "pete ..."
    (lambda name, cats: (
        not _has(r"\bpete\b", name)      # skip all Pete dishes here
        and _has(r"\bbakar(an)?\b|\bpanggang\b", name)
    ), "bakaran"),
    (lambda name, cats: _has(r"\bsteam\b|\bhong ?kong\b|\bnyonya\b|\bgarden\b", name), "steam"),
]


def infer_route_tag(item_name: str, category_path: list[str]) -> str:
    name = _norm(item_name)
    cats = [c.strip() for c in (category_path or [])]

    # --- Priority rules ---
    for cond, tag in PRIORITY_RULES:
        try:
            if cond(name, cats):
                return tag
        except Exception:
            pass

    # --- Protein/keyword-based fallback (technique, base words) ---
    # Ensure “bakar” still beats “udang/cumi” if both appear (handled already above).
    for kw, tag in KEYWORDS.items():
        if kw in name:
            return tag

    # --- Category defaults ---
    if cats:
        top = cats[0]
        if top in CATEGORY_DEFAULTS:
            return CATEGORY_DEFAULTS[top]

    # --- Extra guard: fish default (if ever missed) ---
    if cats and cats[0] == "Ikan":
        return "masak"

    return "dapur"
