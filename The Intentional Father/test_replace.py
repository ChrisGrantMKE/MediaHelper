import bs4
soup = bs4.BeautifulSoup('<p class="text"><span>H</span>ere</p>', 'html.parser')
p = soup.find('p')
p.clear()
p.append('New text')
print(str(p))
