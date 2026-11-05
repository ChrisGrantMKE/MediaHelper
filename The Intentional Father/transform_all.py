import os
import re
import shutil
import bs4

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

# Clean pagebreaks and folio spans from an HTML soup
def clean_pagebreaks_and_folios(soup):
    for span in soup.find_all(attrs={"epub:type": "pagebreak"}):
        span.decompose()
    for span in soup.find_all("span", id=re.compile(r"^page\d+")):
        span.decompose()
    for p in soup.find_all("p", class_=re.compile(r"toc-marker")):
        # If it just contains page numbers or non-narrative markers like "Epigraph" or "Dedication", clean or simplify
        if re.match(r"^[\s\d—\-–\.]+$", p.get_text()):
            p.decompose()

print("Helper defined.")
