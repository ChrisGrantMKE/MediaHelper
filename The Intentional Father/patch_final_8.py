import os
import bs4

DST_TEXT_DIR = r"The Intentional Father\unpacked_secular\OEBPS\Text"

patches = {
    '16-chapter06.xhtml': [
        ('And up there on Anstey',
         "“I was a teenager,” I told him, “only a few years older than you, but I resolved in my heart that I would be a man of vision.” And up there on Anstey’s Hill, I put my hand on my son’s shoulder and spoke words of blessing and vision over him, challenging him to lift his eyes beyond the confines of his generation and see what was truly possible.")
    ],
    '16-chapter07.xhtml': [
        ('True courage means remaining faithful to principles',
         "Courage. The steadfast resolve to confront difficult realities when others flee under pressure. True courage means remaining steadfast to principles and protecting others even when facing severe personal cost.")
    ],
    '18-chapter09.xhtml': [
        ('First exposure to the LGBTQ world.',
         "First exposure to LGBTQ perspectives. How you handle this topic with your child is vital. You’re either going to model basic human empathy, dignity, and respect, or you’re going to pass on judgment, prejudice, and ignorance. I have had this conversation with Nate. We live in Hell’s Kitchen in New York City. I knew I wanted to display genuine human respect and compassion. What’s it going to be for you? How are you approaching this moment?")
    ],
    '18-chapter11.xhtml': [
        ('especially as a Christ follower.',
         "We talked about masturbation, porn, and rape culture. We talked about objectification and violence against women, and how these are inappropriate ways of interacting with women, especially as a man of honor and character.")
    ],
    '20-chapter14.xhtml': [
        ('Also, as someone who has served in youth ministry',
         "Also, as someone who has mentored many teens in the United States, I had seen what happened when they headed straight from high school to college. I felt like so many of them would have benefited from a transitional space, an experience that would give them more time to get ready for adulthood emotionally and mentally. They needed time to mature."),
        ('I was their youth pastor and had been diligent',
         "I had mentored them through high school and had been diligent in coaching them during their senior year. We studied classical philosophy and ethics, and regularly met in the early mornings to discuss character and goals. I’d invested heavily in their lives and had high hopes for them. But during their first week of college, I received frantic calls from two of them. One had made careless decisions at a party, and the other had gotten reckless for the first time. They just weren’t equipped; they were not prepared for what college was going to throw at them. They definitely could have used time between high school and college, but, like so many kids at that age, they were itching to throw off the rules and live with abandon. (Fortunately, both learned from their mistakes and grew into capable, grounded adults.)"),
        ('insight into God’s heart for him',
         "And so, I felt a need to give my son a larger vision of the world before he entered college. I hoped it would provide Nate with greater empathy and a broader understanding of the human condition. I had two concrete goals for this gap year—first, that he would encounter people living in poverty and realize in a visceral way that life wasn’t just about himself. Second, that he wouldn’t jump on the superficial career conveyor belt, prey to an overwhelming feeling that he had to get ahead and do it immediately. A lot of people carry an incredible amount of pressure into their college experience, simply because they don’t have a bigger perspective, a more comprehensive understanding of the world and of themselves."),
        ('the body of Christ rally around you',
         "Once he’d made this decision, it was time to enter the process of fundraising. This became a beautiful moment in and of itself. “Nate,” I said, “you’re going to see an entire community rally around you. You’re going to find out personally about the generosity of human beings when they believe in a young person.” And that’s exactly what happened. He was blown away by how much people believed in him, even people who had never met him in person. He went through a process of real maturity, gratitude, and seeing firsthand what community support can accomplish. That alone made taking a gap year worth it.")
    ]
}

for fname, pair_list in patches.items():
    fpath = os.path.join(DST_TEXT_DIR, fname)
    soup = bs4.BeautifulSoup(open(fpath, encoding='utf-8').read(), 'html.parser')
    for match_sub, replacement in pair_list:
        for tag in soup.find_all(['p', 'blockquote', 'li']):
            txt = ' '.join(tag.get_text().split())
            if match_sub in txt:
                tag.clear()
                tag.append(replacement)
                break
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(str(soup))

print("Patched all 8 remaining entries.")
