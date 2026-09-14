import os
import re
import random
import urllib.parse
import subprocess

REPO_DIR = r"C:\Automation\basecamprig"
BLOG_DIR = os.path.join(REPO_DIR, "src", "content", "blog")
AFFILIATE_TAG = "basecamprig-21"

BUYABLE_PRODUCTS = [
    "tent", "tarp", "sleeping bag", "sleeping pad", "bivy sack", "hammock", "quilt",
    "hardshell jacket", "down jacket", "fleece hoodie", "merino base layer", "trekking pants",
    "hiking boots", "trail running shoes", "wool socks", "gaiters", "gloves",
    "camp stove", "backpacking stove", "titanium pot", "water filter", "water purification tablets",
    "headlamp", "lantern", "power bank", "solar panel", "satellite communicator",
    "bushcraft knife", "folding saw", "camp axe", "multitool", "paracord",
    "trekking poles", "backpack", "dry bag", "bear canister", "first aid kit"
]

def build_amazon_url(query):
    encoded = urllib.parse.quote_plus(f"{query} outdoor gear")
    return f"https://www.amazon.com/s?k={encoded}&tag={AFFILIATE_TAG}"

def patch_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Kontrollera befintliga Amazon-taggar
    existing_tags = len(re.findall(r'amazon\.com/s\?k=', content))
    if existing_tags >= 8:
        print(f"[Skip] {os.path.basename(filepath)} has already {existing_tags} links.")
        return False

    target_count = random.randint(8, 14)
    available_terms = list(BUYABLE_PRODUCTS)
    random.shuffle(available_terms)
    
    injected_count = existing_tags
    used_terms = set()
    
    lines = content.split("\n")
    new_lines = []
    in_frontmatter = False
    frontmatter_count = 0

    for line in lines:
        if line.strip() == "---":
            frontmatter_count += 1
            in_frontmatter = (frontmatter_count < 2)
            new_lines.append(line)
            continue
            
        if in_frontmatter or line.strip().startswith("#") or line.strip().startswith("```"):
            new_lines.append(line)
            continue

        words = line.split(" ")
        modified_words = []
        skip_link = False

        for w in words:
            if "[" in w:
                skip_link = True
            if "]" in w:
                skip_link = False
                modified_words.append(w)
                continue
            if skip_link or injected_count >= target_count:
                modified_words.append(w)
                continue

            clean_word = re.sub(r'[^a-zA-Z]', '', w).lower()
            matched_term = None
            for term in available_terms:
                if term not in used_terms:
                    if clean_word == term or clean_word == term + "s":
                        matched_term = term
                        break

            if matched_term:
                aff_link = build_amazon_url(matched_term)
                linked_word = re.sub(rf'\b{re.escape(clean_word)}\b', f'[{w}]({aff_link})', w, flags=re.IGNORECASE)
                modified_words.append(linked_word)
                used_terms.add(matched_term)
                injected_count += 1
            else:
                modified_words.append(w)

        new_lines.append(" ".join(modified_words))

    updated_content = "\n".join(new_lines)

    # Fallback-sektion om brödtexten inte räckte
    if injected_count < 8:
        needed = target_count - injected_count
        remaining_terms = [t for t in available_terms if t not in used_terms][:needed]
        
        fallback_section = "\n\n### Recommended Field Rig Equipment\n"
        fallback_section += "Field-tested gear setups and verified configurations available on Amazon:\n\n"
        for t in remaining_terms:
            link = build_amazon_url(t)
            fallback_section += f"- [{t.capitalize()} Field Gear Selection]({link})\n"
            injected_count += 1
        
        updated_content += fallback_section

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"[Patched] {os.path.basename(filepath)} -> Now has {injected_count} affiliate links.")
    return True

# Kör igenom alla filer
files = [os.path.join(BLOG_DIR, f) for f in os.listdir(BLOG_DIR) if f.endswith(".md")]
modified = False
for f in files:
    if patch_file(f):
        modified = True

if modified:
    print("[Git] Committing and pushing patched links...")
    subprocess.run(["git", "add", "."], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "commit", "-m", "Inject Amazon affiliate links across existing guides"], cwd=REPO_DIR, check=True)
    subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)
    print("[Done] Retroactive patching complete!")
else:
    print("All existing files already had valid links.")
