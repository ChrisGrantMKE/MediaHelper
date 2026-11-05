import os
import bs4
import zipfile
import shutil

# 1. Clean guide in content.opf
opf_path = r"The Intentional Father\unpacked_secular\OEBPS\content.opf"
soup = bs4.BeautifulSoup(open(opf_path, encoding='utf-8').read(), 'xml')
guide = soup.find('guide')
if guide:
    DROPPED = ['01-cover', '02-half', '03-title', '04-copyright', '06-contents', '21-notes', '23-aboutbarnagroup', '25-ads', '26-bakcov']
    for ref in list(guide.find_all('reference')):
        href = ref.get('href', '')
        if any(d in href for d in DROPPED):
            ref.decompose()
with open(opf_path, 'w', encoding='utf-8') as f:
    f.write(str(soup))

# 2. Clean 05-dedication.xhtml
ded_path = r"The Intentional Father\unpacked_secular\OEBPS\Text\05-dedication.xhtml"
ded_content = """<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head>
    <title>Dedication</title>
    <link href="../Styles/template.css" rel="stylesheet" type="text/css"/>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
  </head>
  <body xml:lang="en-US">
    <div class="Basic-Text-Frame">
      <p class="dedication">For my father, Ian Tyson, whose wisdom, love, and steady support have carried me this far.</p>
    </div>
  </body>
</html>
"""
with open(ded_path, 'w', encoding='utf-8') as f:
    f.write(ded_content)

# 3. Repackage epub
secular_root = r"The Intentional Father\unpacked_secular"
target_epub = r"The Intentional Father\The Intentional Father - Jon Tyson.epub"
secular_epub = r"The Intentional Father\The Intentional Father - Jon Tyson.secular.epub"

with zipfile.ZipFile(secular_epub, 'w') as z:
    mimetype_path = os.path.join(secular_root, 'mimetype')
    z.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
    for root, dirs, files in os.walk(secular_root):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, secular_root)
            if rel_path == 'mimetype':
                continue
            z.write(full_path, rel_path, compress_type=zipfile.ZIP_DEFLATED)

shutil.copyfile(secular_epub, target_epub)
print("Cleaned guide, dedication, and repackaged EPUB successfully!")
