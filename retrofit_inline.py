import os
import re
import random
import urllib.parse
import subprocess

REPO_DIR = r"C:\Automation\basecamprig"
BLOG_DIR = os.path.join(REPO_DIR, "src", "content", "blog")
AFFILIATE_TAG = "basecamprig-21"

# Fraslistan sorteras automatiskt efter längd så att "sleeping bag" matchas före "bag"
TARGET_PHRASES = [
    "backpacking tent", "expedition tent", "tunnel tent", "dome tent", "hot tent", "silnylon tarp",
    "sleeping bag", "mummy bag", "down quilt", "sleeping pad", "foam mat", "camp booties",
    "hardshell jacket", "rain jacket", "down jacket", "fleece hoodie", "merino wool base layer",
    "merino wool", "trekking pants", "hiking boots", "trail running shoes", "merino socks",
    "hiking socks", "gaiters", "camp stove", "backpacking stove", "titanium pot", "cook pot",
    "water filter", "water purification tablets", "gravity water filter", "headlamp", "lantern",
    "power bank", "solar panel", "satellite communicator", "bushcraft knife", "outdoor knife",
    "folding knife", "camp saw", "folding saw", "camp axe", "multitool", "paracord",
    "trekking poles", "backpack", "daypack", "dry bag", "bear canister", "first aid kit",
    "bivy sack", "hammock system"
]

def build_amazon_url(term):
    encoded = urllib.parse.quote_plus(f"{term} outdoor gear")
    return f"https://www.amazon.com/s?k={encoded}&tag={AFFILIATE_TAG}"

def natural_link_replacer(text, min_links=8, max_links=14):
    target_count = random.randint(min_links, max_links)
    
    # Rensa befintliga fallback-sektioner om vi kör om en fil
    text = re.sub(r'\n+### (Recommended Field Rig Equipment|Essential Field Rig).*', '', text, flags=re.DOTALL)
    
    # Räkna befintliga länkar
    existing_links = len(re.findall(r'tag=basecamprig-21', text))
    if existing_links >= target_count:
        return text, existing_links

    # Sortera termer efter längsta fras först så vi matchar "sleeping bag" före "bag"
    sorted_phrases = sorted(TARGET_PHRASES, key=len, reverse=True)
    random.shuffle(sorted_phrases)

    injected = existing_links
    used_terms = set()

    # Försök 1: Ersätt fraser direkt i brödtexten
    # Skydda kodblock, rubriker och befintliga markdown-länkar
    paragraphs = text.split("\n\n")
    new_paragraphs = []

    for p in paragraphs:
        # Rör inte frontmatter, kod eller rubriker
        if p.strip().startswith("---") or p.strip().startswith("```") or p.strip().startswith("#"):
            new_paragraphs.append(p)
            continue

        for phrase in sorted_phrases:
            if injected >= target_count:
                break
            if phrase in used_terms:
                continue

            # Regex: Matcha hela ordet/frasen, men inte inuti [redan länkade](...) hakparenteser
            pattern = rf'(?<!\[)(?<!\w)\b({re.escape(phrase)}s?)\b(?!\w)(?![^\[]*\])'
            match = re.search(pattern, p, flags=re.IGNORECASE)
            if match:
                matched_word = match.group(1)
                url = build_amazon_url(phrase)
                # Ersätt bara den första förekomsten snyggt i texten
                p = re.sub(pattern, f'[{matched_word}]({url})', p, count=1, flags=re.IGNORECASE)
                used_terms.add(phrase)
                injected += 1

        new_paragraphs.append(p)

    # Försök 2: Om texten fortfarande har färre än 8 länkar, fläta in snygga Inline Gear Notes
    if injected < min_links:
        available_fallback = [t for t in TARGET_PHRASES if t not in used_terms]
        random.shuffle(available_fallback)
        
        final_paragraphs = []
        for p in new_paragraphs:
            final_paragraphs.append(p)
            if injected < min_links and len(p) > 150 and not p.strip().startswith(("#", "-", "*", ">")):
                if available_fallback:
                    term = available_fallback.pop()
                    url = build_amazon_url(term)
                    gear_note = f"\n> **Field Rig Pick:** When operating in these environments, reliable [{term.title()}]({url}) is essential for safety and thermal efficiency."
                    final_paragraphs.append(gear_note)
                    injected += 1

        new_paragraphs = final_paragraphs

    return "\n\n".join(new_paragraphs), injected

# Kör igenom alla artiklar
files = [os.path.join(BLOG_DIR, f) for f in os.listdir(BLOG_DIR) if f.endswith(".md")]
modified = False

print("=== STARTAR INLINE-LÄNKNING OCH RETROAKTIV PATCH ===")
for fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        raw = f.read()

    updated, count = natural_link_replacer(raw, min_links=8, max_links=13)
    if updated != raw:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(updated)
        print(f"[OK] {os.path.basename(fpath)} -> Nu {count} infällda länkar.")
        modified = True
    else:
        print(f"[Skippad] {os.path.basename(fpath)} har redan {count} länkar.")

if modified:
    print("\n[Git] Committar och pushar ändringar...")
    subprocess.run(["git", "add", "."], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "commit", "-m", "Inject high-density inline Amazon links across all guides"], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)
    print("Push slutförd till Cloudflare Pages.")
