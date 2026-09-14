import os
import re
import time
import random
import datetime
import subprocess
import urllib.parse
import requests

# --- CONFIGURATION ---
REPO_DIR = r"C:\Automation\basecamprig"
BLOG_DIR = os.path.join(REPO_DIR, "src", "content", "blog")
PROCESSED_FILE = os.path.join(REPO_DIR, "generated_slugs.txt")
AFFILIATE_TAG = "basecamprig-21"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:7b"
INTERVAL_SECONDS = 180 * 60  # 180 minutes
ARTICLES_PER_BATCH = 3

# --- 15,000+ COMBINATION MATRIX (ENGLISH OUTDOOR & BASECAMP GEAR) ---
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
    "weight optimization without sacrificing safety", "field maintenance, drying and tear repair guide",
    "preventing internal condensation and moisture buildup", "packing methodology and gear longevity tips",
    "membrane breathability vs wind resistance comparison", "temperature ratings and true comfort limits",
    "long-term durability analysis in harsh conditions", "essential accessories and modular rig configuration"
]

BUYABLE_TERMS = [
    "backpacking tent", "tunnel tent", "4 season tent", "camping tarp", "down sleeping bag",
    "synthetic sleeping bag", "sleeping pad", "insulated sleeping mat", "hardshell jacket",
    "trekking pants", "hiking boots", "trail running shoes", "merino base layer", "wool socks",
    "down jacket", "fleece pullover", "gaiters", "camp stove", "backpacking stove", "multi fuel stove",
    "headlamp", "trekking poles", "hiking backpack", "daypack", "dry bag", "water filter",
    "bushcraft knife", "folding saw", "camp hatchet", "power bank", "solar charger",
    "insulated thermos", "tent stakes", "paracord", "compass", "first aid kit", "mosquito net",
    "freeze dried meals", "titanium cookware", "camping hammock", "stuff sack", "bivy sack"
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
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        print(f"[Ollama Error] {e}")
        return None

def inject_affiliate_links(markdown_text, min_links=8, max_links=15):
    """Replaces between 8 and 15 unique buyable terms with Amazon search links."""
    target_count = random.randint(min_links, max_links)
    chosen_terms = random.sample(BUYABLE_TERMS, min(target_count, len(BUYABLE_TERMS)))
    
    injected = 0
    lines = markdown_text.split("\n")
    processed_lines = []

    for line in lines:
        # Avoid headings, frontmatter, and already linked table rows
        if line.startswith("#") or line.startswith("---") or "| [" in line:
            processed_lines.append(line)
            continue

        for term in list(chosen_terms):
            if injected >= target_count:
                break
            
            # Match whole word, ensure not already inside markdown link
            pattern = rf'(?i)\b({re.escape(term)})\b(?![^\[]*\])'
            match = re.search(pattern, line)
            if match:
                matched_word = match.group(1)
                search_query = urllib.parse.quote_plus(matched_word.lower())
                aff_url = f"https://www.amazon.se/s?k={search_query}&tag={AFFILIATE_TAG}"
                replacement = f"[{matched_word}]({aff_url})"
                line = line[:match.start()] + replacement + line[match.end():]
                chosen_terms.remove(term)
                injected += 1

        processed_lines.append(line)

    return "\n".join(processed_lines), injected

def create_article():
    title, main_eq = generate_topic()
    slug = slugify(title)
    
    os.makedirs(BLOG_DIR, exist_ok=True)
    slug_history = set()
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            slug_history = set(f.read().splitlines())

    if slug in slug_history:
        print(f"Skipping duplicate slug: {slug}")
        return False

    prompt = f"""Write an in-depth, highly technical and practical outdoor and basecamp field guide in English with the title: "{title}".

Requirements:
1. Write at least 750 words in fluent, professional English.
2. Use clean Markdown structure with headings (## and ###), bullet lists, and at least one technical comparison table.
3. Mention exact material specs (e.g., hydrostatic head mm, Denier ratings, R-value, fill power down vs synthetic, membrane breathability) and hands-on field protocols.
4. DO NOT write fluff intros like "Welcome to this guide" or meta summaries. Start immediately with a hard-hitting, fact-dense first paragraph.
5. Toward the bottom, include a Markdown table recommending 4-5 core gear choices with their field roles.
"""

    print(f"\n[Ollama] Generating: {title}")
    raw_content = query_ollama(prompt)
    if not raw_content or len(raw_content) < 300:
        print("[Error] Ollama returned insufficient content.")
        return False

    # Inject affiliate links
    final_content, link_count = inject_affiliate_links(raw_content, min_links=8, max_links=15)
    print(f"[Affiliate] Injected {link_count} affiliate links.")

    date_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    description = f"Technical field guide on {main_eq}. Engineering parameters, gear setups, and durability optimizations for harsh conditions."

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
        print("[Git] Push completed. Cloudflare Pages build triggered.")
    except subprocess.CalledProcessError as e:
        print(f"[Git Error] {e}")

def run_loop():
    print("=== BasecampRig pSEO Engine Started ===")
    print(f"Generating {ARTICLES_PER_BATCH} English guides every {INTERVAL_SECONDS // 60} minutes.")
    
    while True:
        created = 0
        for i in range(ARTICLES_PER_BATCH):
            print(f"\nGenerating article {i+1}/{ARTICLES_PER_BATCH}...")
            if create_article():
                created += 1
            time.sleep(5)
            
        if created > 0:
            git_sync()

        print(f"\n[Sleeping] Batch complete. Pausing for {INTERVAL_SECONDS // 60} minutes until next cycle...")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    run_loop()
