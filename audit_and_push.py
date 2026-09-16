import os
import re
import random
import urllib.parse
import subprocess

REPO_DIR = r"C:\Automation\basecamprig"
BLOG_DIR = os.path.join(REPO_DIR, "src", "content", "blog")
AFFILIATE_TAG = "basecamprig-21"

GEAR_TERMS = [
    "backpacking tent", "4-season expedition tent", "ultralight silnylon tarp",
    "down sleeping bag", "sub-zero winter mummy bag", "insulated sleeping pad",
    "down camp booties", "3-layer hardshell jacket", "waterproof rain jacket",
    "packable down jacket", "merino wool thermal base layer", "reinforced trekking pants",
    "waterproof hiking boots", "trail running shoes", "merino wool hiking socks",
    "canister backpacking stove", "titanium cook pot", "gravity camp water filter",
    "water purification tablets", "rechargeable headlamp", "camp lantern",
    "rugged field power bank", "foldable solar panel charger", "bushcraft fixed blade knife",
    "carbon steel folding knife", "compact folding camp saw", "lightweight camp hatchet",
    "carbon fiber trekking poles", "65L internal frame trekking pack", "waterproof roll-top dry bag",
    "bear-resistant food canister", "wilderness trauma medical kit", "emergency storm shelter bivy"
]

def build_amazon_url(item):
    encoded = urllib.parse.quote_plus(f"{item} outdoor gear")
    return f"https://www.amazon.com/s?k={encoded}&tag={AFFILIATE_TAG}"

files = [os.path.join(BLOG_DIR, f) for f in os.listdir(BLOG_DIR) if f.endswith(".md")]

print("=" * 70)
print("1. KÖR STATUSCHECK (FÖRE PATCH)")
print("=" * 70)

status_report = []
for fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    count = len(re.findall(r'tag=basecamprig-21', content))
    status_report.append((fpath, count))
    status_str = "[GODKÄND]" if count >= 8 else "[FÖR FÅ]  "
    print(f"{status_str} {os.path.basename(fpath)}: {count} länkar")

print("\n" + "=" * 70)
print("2. PATCHNING AV ARTIKLAR MED UNDER 8 LÄNKAR")
print("=" * 70)

modified = False
for fpath, count in status_report:
    if count < 8:
        target = random.randint(9, 12)
        needed = target - count
        
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            
        shuffled = list(GEAR_TERMS)
        random.shuffle(shuffled)
        
        paragraphs = content.split("\n\n")
        new_paragraphs = []
        added = 0
        used = set()

        for p in paragraphs:
            if p.strip().startswith("---") or p.strip().startswith("#"):
                new_paragraphs.append(p)
                continue

            for term in shuffled:
                if added >= needed:
                    break
                if term in used:
                    continue

                pattern = rf'(?<!\[)(?<!\w)\b({re.escape(term)}s?)\b(?!\w)(?![^\[]*\])'
                if re.search(pattern, p, flags=re.IGNORECASE):
                    url = build_amazon_url(term)
                    p = re.sub(pattern, rf'[\1]({url})', p, count=1, flags=re.IGNORECASE)
                    added += 1
                    used.add(term)

            new_paragraphs.append(p)

        content = "\n\n".join(new_paragraphs)

        if (count + added) < 8:
            still_needed = 9 - (count + added)
            rig_bullets = []
            for term in shuffled:
                if still_needed <= 0:
                    break
                if term in used:
                    continue
                url = build_amazon_url(term)
                rig_bullets.append(f"- [{term.title()} Field Rig Selection]({url})")
                still_needed -= 1
                added += 1
                used.add(term)

            addon = "\n\n### Essential Field Rig Equipment\n"
            addon += "Field-verified components and high-durability gear configurations:\n\n"
            addon += "\n".join(rig_bullets) + "\n"
            content = content.rstrip() + addon

        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)

        final_c = len(re.findall(r'tag=basecamprig-21', content))
        print(f"[FIXAD] {os.path.basename(fpath)}: {count} -> {final_c} länkar")
        modified = True

print("\n" + "=" * 70)
print("3. KONTROLL AV SLUTRESULTAT")
print("=" * 70)

all_passed = True
for fpath in files:
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
    count = len(re.findall(r'tag=basecamprig-21', content))
    if count < 8:
        all_passed = False
        print(f"[FEL] {os.path.basename(fpath)}: Endast {count} länkar!")

if all_passed:
    print(f"Alla {len(files)} artiklar uppfyller nu kravet (minst 8 affiliatelänkar)!")

if modified:
    print("\n" + "=" * 70)
    print("4. AUTOPUSH TILL GITHUB & CLOUDFLARE PAGES")
    print("=" * 70)
    subprocess.run(["git", "add", "."], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "commit", "-m", "Guarantee min 8 affiliate links per article and push to live"], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)
    print("[KLART] Alla ändringar är pushade och byggs nu live på Cloudflare!")
else:
    print("\nInga filer behövde ändras. Repot är redan synkat och godkänt.")
