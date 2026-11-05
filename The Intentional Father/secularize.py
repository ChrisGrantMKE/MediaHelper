import os
import re
import shutil
import zipfile
import bs4

SRC_DIR = r"The Intentional Father\unpacked"
DST_DIR = r"The Intentional Father\unpacked_secular"

# Terms to audit
TERMS = [
    r'\bgod\b', r'\bgod\'?s\b', r'\blord\b', r'\bjesus\b', r'\bchrist\b', r'\bchristian(s|ity)?\b',
    r'\bbible\b', r'\bbiblical\b', r'\bscripture(s)?\b', r'\bpray(er|ers|ed|ing)?\b',
    r'\bchurch(es)?\b', r'\bfaith\b', r'\bfaithful(ness)?\b', r'\bspiritual(ity)?\b',
    r'\bpastor\b', r'\bdisciple(s|ship)?\b', r'\bworship\b', r'\bgospel\b', r'\bholy\b',
    r'\bministry\b', r'\bapostolic\b', r'\bprophetic\b', r'\bevangelistic\b'
]
AUDIT_REGEX = re.compile('|'.join(TERMS), re.IGNORECASE)

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

print("Setup ready.")
