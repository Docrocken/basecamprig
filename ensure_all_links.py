import os
import re
import random
import urllib.parse
import subprocess

REPO_DIR = r"C:\Automation\basecamprig"
BLOG_DIR = os.path.join(REPO_DIR, "src", "content", "blog")
AFFILIATE_TAG = "basecamprig-21"

GEAR_TARGETS = [
    "backpacking tent", "4-season tent", "silnylon rain tarp", "down sleeping bag",
    "winter mummy bag", "insulated sleeping pad", "camp booties", "hardshell jacket",
    "waterproof rain jacket", "packable down jacket", "merino wool thermal base layer",
    "trekking pants", "hiking boots", "trail running shoes", "merino wool hiking socks",
    "canister backpacking stove", "titanium cook pot", "gravity camp water filter",
    "water purification tablets", "rechargeable headlamp", "camp lantern",
    "rugged field power bank", "foldable solar panel charger", "bushcraft fixed blade knife",
    "carbon steel folding knife", "compact camp saw", "camp hatchet", "multitool",
    "carbon fiber trekking poles", "internal frame trekking pack", "waterproof dry bag",
    "bear resistant food canister", "wilderness trauma first aid kit", "emergency storm bivy"
]

def build_amazon_url(item):
    encoded = urllib.parse.quote_plus(f"{item} outdoor gear")
    return f"https://www.amazon.com/s?k={encoded}&tag={AFFILIATE_TAG}"

files = [os.path.join(BLOG_DIR, f) for f in os.listdir(BLOG_DIR) if f.endswith(".md")]
modified = False

print("=== VERIFIERAR OCH TÄTNINGS-PATCHA ALLA ARTIKLAR ===")

for fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    # Räkna unika/befintliga länkar med affiliatetaggen
    current_count = len(re.findall(r'tag=basecamprig-21', content))
    
    if current_count < 8:
        needed = random.randint(9, 12) - current_count
        shuffled_gear = list(GEAR_TARGETS)
        random.shuffle(shuffled_gear)
        
        # 1. Försök matcha naturligt i brödtexten först (utan längdbegränsning)
        paragraphs = content.split("\n\n")
        new_paragraphs = []
        added = 0

        for p in paragraphs:
            # Rör inte frontmatter eller rubriker
            if p.strip().startswith("---") or p.strip().startswith("#"):
                new_paragraphs.append(p)
                continue

            for gear in shuffled_gear:
                if added >= needed:
                    break
                # Matcha frasen case-insensitive om den inte redan är i en länk
                pattern = rf'(?<!\[)(?<!\w)\b({re.escape(gear)}s?)\b(?!\w)(?![^\[]*\])'
                if re.search(pattern, p, flags=re.IGNORECASE):
                    url = build_amazon_url(gear)
                    p = re.sub(pattern, rf'[\1]({url})', p, count=1, flags=re.IGNORECASE)
                    added += 1

            new_paragraphs.append(p)

        content = "\n\n".join(new_paragraphs)

        # 2. Om det FORTFARANDE behövs fler länkar för att nå minst 8:
        if (current_count + added) < 8:
            still_needed = 9 - (current_count + added)
            callouts = []
            for gear in shuffled_gear:
                if still_needed <= 0:
                    break
                url = build_amazon_url(gear)
                callouts.append(f"- [{gear.title()} Field Rig Selection]({url})")
                still_needed -= 1
                added += 1

            addon = "\n\n### Essential Field Rig Equipment\n"
            addon += "Field-verified components and high-durability gear configurations:\n\n"
            addon += "\n".join(callouts) + "\n"
            content = content.rstrip() + addon

        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)

        final_total = len(re.findall(r'tag=basecamprig-21', content))
        print(f"[FIXAD] {os.path.basename(fpath)}: {current_count} -> {final_total} länkar.")
        modified = True
    else:
        print(f"[OK] {os.path.basename(fpath)}: {current_count} länkar.")

if modified:
    print("\n[Git] Committar och pushar till GitHub/Cloudflare...")
    subprocess.run(["git", "add", "."], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "commit", "-m", "Guarantee 100% affiliate link compliance across all guides"], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)
    print("Synkning klar!")
else:
    print("\nAlla artiklar är redan 100 % godkända.")
