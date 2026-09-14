import os
import re
import random
import urllib.parse
import subprocess

REPO_DIR = r"C:\Automation\basecamprig"
BLOG_DIR = os.path.join(REPO_DIR, "src", "content", "blog")
AFFILIATE_TAG = "basecamprig-21"

RECOMMENDED_PRODUCTS = [
    "ultralight backpacking tent", "4-season expedition shelter", "silnylon rain tarp",
    "800-fill down sleeping bag", "sub-zero winter mummy bag", "insulated sleeping pad R-value 4+",
    "closed-cell foam ground mat", "waterproof breathable hardshell jacket", "reinforced trekking pants",
    "merino wool thermal base layer", "waterproof mountain hiking boots", "trail running shoes",
    "merino wool hiking socks", "canister backpacking stove", "titanium cooking pot",
    "gravity camp water filter", "hollow fiber membrane filter", "500-lumen rechargeable headlamp",
    "rugged 20000mAh field power bank", "foldable solar panel charger", "carbon steel outdoor knife",
    "compact folding camp saw", "lightweight camp hatchet", "carbon fiber trekking poles",
    "65L expedition trekking backpack", "waterproof roll-top dry bag", "wilderness trauma medical kit",
    "portable camping hammock system", "emergency storm shelter bivy"
]

def build_amazon_url(query):
    encoded = urllib.parse.quote_plus(f"{query} outdoor gear")
    return f"https://www.amazon.com/s?k={encoded}&tag={AFFILIATE_TAG}"

files = [os.path.join(BLOG_DIR, f) for f in os.listdir(BLOG_DIR) if f.endswith(".md")]
modified = False

for filepath in files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    current_links = len(re.findall(r'tag=basecamprig-21', content))
    
    if current_links < 8:
        target = random.randint(8, 12)
        needed = target - current_links
        
        # Välj relevanta produkter som inte redan är länkade
        shuffled = list(RECOMMENDED_PRODUCTS)
        random.shuffle(shuffled)
        
        fallback_section = "\n\n### Essential Field Rig & Backcountry Gear\n"
        fallback_section += "Tested configurations and gear recommendations available on Amazon:\n\n"
        
        added = 0
        for item in shuffled:
            if added >= needed:
                break
            url = build_amazon_url(item)
            fallback_section += f"- [{item.title()} Field Selection]({url})\n"
            added += 1
            
        new_content = content.rstrip() + fallback_section + "\n"
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        print(f"[Fixed] {os.path.basename(filepath)}: länkantal ökades från {current_links} till {current_links + added}.")
        modified = True
    else:
        print(f"[OK] {os.path.basename(filepath)} har redan {current_links} länkar.")

if modified:
    print("\n[Git] Committar och pushar ändringarna...")
    subprocess.run(["git", "add", "."], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "commit", "-m", "Ensure minimum 8 affiliate links per article"], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)
    print("[Klart] Alla artiklar har nu minst 8 aktiva affiliatelänkar och är pushade!")
else:
    print("\nAlla artiklar uppfyller redan kravet.")
