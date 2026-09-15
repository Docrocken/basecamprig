import os
import re
import time
import random
import datetime
import subprocess
import urllib.parse
import requests

REPO_DIR = r"C:\Automation\basecamprig"
BLOG_DIR = os.path.join(REPO_DIR, "src", "content", "blog")
PROCESSED_FILE = os.path.join(REPO_DIR, "generated_slugs.txt")
AFFILIATE_TAG = "basecamprig-21"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"
INTERVAL_SECONDS = 180 * 60
ARTICLES_PER_BATCH = 3

EQUIPMENT_CORE = [
    "2-person backpacking tent", "4-season expedition tunnel tent", "ultralight freestanding dome tent",
    "geodesic alpine storm tent", "ultralight silnylon tarp 10x10", "hot tent with stove jack",
    "3-season 800-fill down sleeping bag", "sub-zero winter mummy bag", "ultralight synthetic sleeping bag",
    "insulated inflatable sleeping pad R-value 4+", "closed-cell foam sleeping mat", "down camp booties",
    "3-layer waterproof breathable hard shell jacket", "reinforced trekking pants", "merino wool thermal base layer",
    "synthetic grid fleece mid-layer", "packable ultralight down jacket", "waterproof mountain trekking boots",
    "breathable trail running shoes", "merino wool hiking socks", "snow and mud gaiters",
    "canister stove system", "liquid fuel expedition stove", "ultralight wood burning titanium stove",
    "gravity camp water filter", "hollow fiber membrane filter pump", "insulated titanium cook pot",
    "500-lumen rechargeable headlamp", "rugged 20000mAh field power bank", "foldable solar panel charger",
    "full-tang bushcraft fixed blade", "carbon steel folding outdoor knife", "compact folding camp saw",
    "packable camp hatchet", "carbon fiber trekking poles", "65L internal frame trekking pack",
    "30L daypack with load lifters", "roll-top waterproof dry bags", "wilderness trauma medical kit",
    "collapsible camp trenching shovel", "bear-resistant food canister", "portable camping hammock system",
    "down camping quilt 20F", "ultralight bivy sack", "high-altitude glacier sunglasses",
    "paracord ridge line and tensioners", "windproof storm matches and ferro rod", "collapsible 10L camp water bladder"
]

CONDITIONS_CONTEXT = [
    "in severe alpine storm winds", "during torrential continuous rain", "in sub-zero winter freeze and snow",
    "under early spring wet snow slush", "in humid bog and swamp terrain", "above the tree line on exposed ridges",
    "on long-distance solo thru-hikes", "at remote winter basecamp setups", "during multi-day backcountry trekking",
    "across rocky scree and steep mountain passes", "on fast-and-light packrafting expeditions", "at off-grid vehicle basecamps",
    "through dense boreal forest", "during sudden shoulder-season temperature drops", "in desert canyon flash-freeze environments"
]

FOCUS_ANGLES = [
    "complete field selection and material breakdown", "waterproof hydrostatic head and abrasion test",
    "weight optimization without sacrificing safety", "field maintenance drying and tear repair guide",
    "preventing internal condensation and moisture buildup", "packing methodology and gear longevity tips",
    "membrane breathability vs wind resistance comparison", "temperature ratings and true comfort limits",
    "long-term durability analysis in harsh conditions", "essential accessories and modular rig configuration"
]

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

def generate_topic():
    eq = random.choice(EQUIPMENT_CORE)
    cond = random.choice(CONDITIONS_CONTEXT)
    angle = random.choice(FOCUS_ANGLES)
    title = f"{eq.capitalize()} {cond}: {angle.capitalize()}"
    return title, eq

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:70]

def query_ollama(prompt):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "top_p": 0.9}
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        print(f"[Ollama Error] {e}")
        return None

def build_amazon_url(term):
    encoded = urllib.parse.quote_plus(f"{term} outdoor gear")
    return f"[https://www.amazon.com/s?k=](https://www.amazon.com/s?k=){encoded}&tag={AFFILIATE_TAG}"

def inject_inline_links(text, min_links=8, max_links=14):
    target_count = random.randint(min_links, max_links)
    sorted_phrases = sorted(TARGET_PHRASES, key=len, reverse=True)
    random.shuffle(sorted_phrases)

    injected = 0
    used_terms = set()
    paragraphs = text.split("\n\n")
    new_paragraphs = []

    for p in paragraphs:
        if p.strip().startswith("---") or p.strip().startswith("```") or p.strip().startswith("#"):
            new_paragraphs.append(p)
            continue

        for phrase in sorted_phrases:
            if injected >= target_count:
                break
            if phrase in used_terms:
                continue

            pattern = rf'(?<!\[)(?<!\w)\b({re.escape(phrase)}s?)\b(?!\w)(?![^\[]*\])'
            match = re.search(pattern, p, flags=re.IGNORECASE)
            if match:
                matched_word = match.group(1)
                url = build_amazon_url(phrase)
                p = re.sub(pattern, f'[{matched_word}]({url})', p, count=1, flags=re.IGNORECASE)
                used_terms.add(phrase)
                injected += 1

        new_paragraphs.append(p)

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
                    gear_note = f"\n> **Field Rig Pick:** For harsh field exposure, verified [{term.title()}]({url}) provides reliable durability and safety margins."
                    final_paragraphs.append(gear_note)
                    injected += 1
        new_paragraphs = final_paragraphs

    return "\n\n".join(new_paragraphs), injected

def create_article():
    title, main_eq = generate_topic()
    slug = slugify(title)
    
    os.makedirs(BLOG_DIR, exist_ok=True)
    slug_history = set()
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            slug_history = set(f.read().splitlines())

    if slug in slug_history:
        print(f"Skipping duplicate: {slug}")
        return False

    prompt = f"""Write an in-depth, highly technical outdoor and basecamp field guide in English with the title: "{title}".

Requirements:
1. Write 750-1000 words in fluent, authoritative English.
2. Structure with clean Markdown (## and ### headings, technical breakdown, specification table).
3. Mention exact engineering specs (hydrostatic head mm, fabric Denier, R-value, fill power, breathability).
4. Do NOT use introductory fluff like "In this article". Start directly with high-density field analysis.
5. In the body text, naturally mention relevant gear items (tents, boots, hardshell jackets, camp stoves, sleeping bags, backpacks, headlamps, water filters).
"""

    print(f"\n[Ollama] Generating: {title}")
    raw_content = query_ollama(prompt)
    if not raw_content or len(raw_content) < 300:
        print("[Error] Incomplete output from Ollama.")
        return False

    final_content, link_count = inject_inline_links(raw_content, min_links=8, max_links=14)
    print(f"[Affiliate] Injected {link_count} inline Amazon links.")

    date_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    description = f"Technical field guide on {main_eq}. Engineering parameters, gear setups, and durability optimizations for harsh backcountry conditions."

    frontmatter = f"""---
title: "{title.replace('\"', '')}"
description: "{description.replace('\"', '')}"
pubDate: "{date_now}"
category: "Gear & Field Setups"
---

{final_content}
"""

    filename = f"{datetime.date.today().isoformat()}-{slug}.md"
    filepath = os.path.join(BLOG_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter)

    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(slug + "\n")

    print(f"[Saved] {filename}")
    return True

def git_sync():
    try:
        print("[Git] Pushing batch to GitHub...")
        subprocess.run(["git", "add", "."], cwd=REPO_DIR, check=True)
        commit_msg = f"Auto-publish batch: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)
        print("[Git] Push completed.")
    except subprocess.CalledProcessError as e:
        print(f"[Git Error] {e}")

def run_loop():
    print("=== BasecampRig pSEO Engine Started (Inline Affiliate Injection) ===")
    while True:
        created = 0
        for i in range(ARTICLES_PER_BATCH):
            print(f"\n[Batch Item {i+1}/{ARTICLES_PER_BATCH}]")
            if create_article():
                created += 1
            time.sleep(5)
            
        if created > 0:
            git_sync()

        print(f"\n[Sleeping] Pausing {INTERVAL_SECONDS // 60} minutes until next cycle...")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    run_loop()
