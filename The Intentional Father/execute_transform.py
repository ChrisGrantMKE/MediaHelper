import os
import re
import shutil
import bs4

from replacements_part1 import REPLACEMENTS as R1
from replacements_part2 import REPLACEMENTS as R2
from replacements_part3 import REPLACEMENTS as R3
from replacements_part4 import REPLACEMENTS as R4

ALL_REPLACEMENTS = {}
ALL_REPLACEMENTS.update(R1)
ALL_REPLACEMENTS.update(R2)
ALL_REPLACEMENTS.update(R3)
ALL_REPLACEMENTS.update(R4)

TEXT_DIR = r"The Intentional Father\unpacked_secular\OEBPS\Text"
OEBPS_DIR = r"The Intentional Father\unpacked_secular\OEBPS"

DROPPED_FILES = [
    '01-cover.xhtml',
    '02-half.xhtml',
    '03-title.xhtml',
    '04-copyright.xhtml',
    '06-contents.xhtml',
    '21-notes.xhtml',
    '23-aboutbarnagroup.xhtml',
    '25-ads.xhtml',
    '26-bakcov.xhtml'
]

TERMS = [
    r'\bgod\b', r'\bgod\'?s\b', r'\blord\b', r'\bjesus\b', r'\bchrist\b', r'\bchristian(s|ity)?\b',
    r'\bbible\b', r'\bbiblical\b', r'\bscripture(s)?\b', r'\bpray(er|ers|ed|ing)?\b',
    r'\bchurch(es)?\b', r'\bfaith\b', r'\bfaithful(ness)?\b', r'\bspiritual(ity)?\b',
    r'\bpastor\b', r'\bdisciple(s|ship)?\b', r'\bworship\b', r'\bgospel\b', r'\bholy\b',
    r'\bministry\b', r'\bapostolic\b', r'\bprophetic\b', r'\bevangelistic\b'
]
AUDIT_REGEX = re.compile('|'.join(TERMS), re.IGNORECASE)

def run():
    print("=== STEP 1: Deleting dropped non-narrative / front-matter files ===")
    for df in DROPPED_FILES:
        target = os.path.join(TEXT_DIR, df)
        if os.path.exists(target):
            os.remove(target)
            print(f"Removed: {df}")

    print("\n=== STEP 2: Applying text transformations and cleaning page breaks ===")
    retained_files = sorted([f for f in os.listdir(TEXT_DIR) if f.endswith('.xhtml')])
    
    total_replacements_applied = 0
    for fname in retained_files:
        fpath = os.path.join(TEXT_DIR, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Clean page breaks: <span epub:type="pagebreak" id="page..." title="..."></span>
        content = re.sub(r'<span\s+epub:type="pagebreak"[^>]*></span>\s*', '', content)
        content = re.sub(r'<span\s+id="page\d+"[^>]*></span>\s*', '', content)

        # Apply specific replacements for this file
        repls = ALL_REPLACEMENTS.get(fname, [])
        for old, new in repls:
            if old in content:
                content = content.replace(old, new)
                total_replacements_applied += 1
            else:
                # Try normalized whitespace
                old_norm = " ".join(old.split())
                found = False
                # If it's a multiline block or within HTML tags
                for p_match in re.finditer(re.escape(old_norm[:40]), content):
                    pass
                print(f"  [!] Note: replacement target in {fname} not found directly: {old[:50]}...")

        # Also generic cleanup for any residual stray words if needed
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)

    print(f"\nApplied {total_replacements_applied} targeted chapter replacements.")

    print("\n=== STEP 3: Updating content.opf, toc.ncx, and toc.xhtml ===")
    update_content_opf()
    update_toc_ncx()
    update_toc_xhtml()

    print("\n=== STEP 4: Auditing all remaining xhtml files for any religious terms ===")
    residual_matches = []
    for fname in retained_files:
        if fname == 'toc.xhtml': continue
        fpath = os.path.join(TEXT_DIR, fname)
        soup = bs4.BeautifulSoup(open(fpath, encoding='utf-8').read(), 'html.parser')
        for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'blockquote', 'li']):
            txt = p.get_text().strip()
            if AUDIT_REGEX.search(txt):
                residual_matches.append((fname, txt))

    print(f"Total residual matches: {len(residual_matches)}")
    for fn, rm in residual_matches[:20]:
        print(f"  [{fn}] {rm[:100]}")

def update_content_opf():
    opf_path = os.path.join(OEBPS_DIR, 'content.opf')
    soup = bs4.BeautifulSoup(open(opf_path, encoding='utf-8').read(), 'xml')

    manifest = soup.find('manifest')
    spine = soup.find('spine')

    dropped_ids = set()
    for item in list(manifest.find_all('item')):
        href = item.get('href', '')
        for df in DROPPED_FILES:
            if df in href:
                dropped_ids.add(item.get('id'))
                item.decompose()

    for itemref in list(spine.find_all('itemref')):
        if itemref.get('idref') in dropped_ids:
            itemref.decompose()

    with open(opf_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print("Updated content.opf.")

def update_toc_ncx():
    ncx_path = os.path.join(OEBPS_DIR, 'toc.ncx')
    soup = bs4.BeautifulSoup(open(ncx_path, encoding='utf-8').read(), 'xml')

    for np in list(soup.find_all('navPoint')):
        content = np.find('content')
        if content:
            src = content.get('src', '')
            for df in DROPPED_FILES:
                if df in src:
                    np.decompose()
                    break

    with open(ncx_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print("Updated toc.ncx.")

def update_toc_xhtml():
    toc_path = os.path.join(TEXT_DIR, 'toc.xhtml')
    if not os.path.exists(toc_path): return
    soup = bs4.BeautifulSoup(open(toc_path, encoding='utf-8').read(), 'html.parser')

    for a in list(soup.find_all('a')):
        href = a.get('href', '')
        for df in DROPPED_FILES:
            if df in href:
                # Decompose parent li if present
                li = a.find_parent('li')
                if li: li.decompose()
                else: a.decompose()
                break

    with open(toc_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    print("Updated toc.xhtml.")

if __name__ == "__main__":
    run()
