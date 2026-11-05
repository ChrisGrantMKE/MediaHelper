import os
import re
import shutil
import bs4

SRC_TEXT_DIR = r"The Intentional Father\unpacked\OEBPS\Text"
DST_TEXT_DIR = r"The Intentional Father\unpacked_secular\OEBPS\Text"
DST_OEBPS_DIR = r"The Intentional Father\unpacked_secular\OEBPS"

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

# Comprehensive dictionary mapping (filename, match_predicate_fn) -> new_text_generator
# We match by identifying substrings in normalized paragraph text.
RULES = {
    '05-dedication.xhtml': [
        (lambda t: "whose prayers have carried me this far" in t,
         "whose wisdom, love, and steady support have carried me this far."),
        (lambda t: "Dedication" in t and len(t) < 15,
         None), # remove tag
        (lambda t: "For my fath" in t,
         "For my father, Ian Tyson,")
    ],
    '07-foreword.xhtml': [
        (lambda t: "Why is it so hard to disciple young men" in t,
         "“Why is it so hard to mentor young men?” “What can we do to make a real difference in the lives of our sons?”"),
        (lambda t: "urgent matters for Christians today" in t,
         "I believe that answering these questions—thinking through the nature of the challenges they represent and turning our hearts, minds, and hands to solutions—is one of the urgent matters for parents, mentors, and communities today."),
        (lambda t: "Not to mention the many roadblocks" in t and "faith" in t,
         "Here’s why: based on research, our society is facing a crisis of raising boys into men of character and consequence—that is, young men who live with integrity and make a positive impact with their lives. Whether we’re talking about the powerful allure of video games and entertainment, the harmful forces of toxic masculinity, major disruptions to finding a vocation and work, questions of sex and sexuality, the phenomenon of digital-access porn, or the paucity of good role models for young men, the obstacles seem stacked against young men. Not to mention the many roadblocks and speed bumps on the path to a young man owning his values in today’s chaotic media ecosystem where young people are shaped by the relentless algorithms of modern entertainment."),
        (lambda t: "churches aren’t helping us fathers" in t,
         "And too often, as you’ll see throughout this book, standard cultural institutions aren’t helping us fathers find a better way. Research shows that fathers everywhere are thinking about and experiencing parenting in much the same way as everyone else: uncertain, overwhelmed, trying their best but not sure they’re making a difference."),
        (lambda t: "truly sacred. I pray this book" in t,
         "My friendship with Zack has blossomed over the years. His curiosity and strength inspire me, and our closeness forms a deep well of resilience for us both. I still have so much to learn, but with Jon’s help, I’m convinced that, in working to become an intentional father, I have entered into a profound, life-defining calling. I hope this book will help you experience some of the deepest joys you can imagine with your son, as I have with mine.")
    ],
    '12-chapter01.xhtml': [
        (lambda t: "derive his image of God" in t,
         "That was one of the most sobering drives of my entire life. Even after returning to work, I couldn’t stop thinking about this baby boy soon to come into the world. He would look to me to find a model of manhood and would in many ways derive his earliest understanding of moral authority, security, and love from our relationship. I wasn’t sure I was ready for that. I wasn’t convinced I had been raised properly—how could I possibly have the necessary tools and knowledge to raise a son with true integrity, honor, and purpose?"),
        (lambda t: "practicing Christians" in t and "worship service" in t,
         "Throughout The Intentional Father you’ll find stats, charts, and other data visualizations based on research among U.S. fathers of children, teens, or young adults ages ten to twenty-five, drawn from a nationally representative group of 1,058 dads across America. Across all backgrounds, fathers just like you are doing their best to parent on purpose."),
        (lambda t: "raise your child in a God-honoring way" in t,
         "And because of that determination, because of that desire, I want to affirm you and honor you for your willingness to do the work, for looking around, and for trying to figure out how to raise your child with deep integrity, honor, and moral purpose."),
        (lambda t: "God-honoring way of being a man" in t,
         "How can we do this? How can we raise our sons into healthy masculinity, into a virtuous and honorable way of being a man?"),
        (lambda t: "practicing Christian fathers are a bit more likely" in t,
         "Half of all U.S. dads say they did not feel fully prepared for fatherhood before their child came into the world, underscoring the universal need for deliberate preparation and mentorship.")
    ],
    '12-chapter02.xhtml': [
        (lambda t: "why God gave them to him" in t,
         "There is the involved father. This type of dad shows up at sporting events and takes the time to put safety filters on his kids’ devices. He gets a lot of things right, but because of the busyness of life and the failure to ask the right questions, he never seeks to understand specifically who his children are, what makes them tick, and what potential lies within them. This is a noble dad, but one haunted by the sense that there is something more, another layer or level in his parenting."),
        (lambda t: "redemptive potential" in t and "God has given him" in t,
         "The intentional father is deeply invested in discovering who his children are and how he can help them reach their fullest potential. He seeks to understand the children in his care and wants to form them into young persons who can fulfill their unique purpose. He sees parenting as central to his highest moral calling and embraces it with all of his might. This kind of father leaves an enduring, multigenerational legacy in the lives of his children."),
        (lambda t: "ONE SEGMENT of the United States" in t and "youth pastor" in t,
         "THERE IS ONE COMMUNITY in the United States that has historically maintained an intentional structure for raising young men, and they even have a clear path in place to facilitate it. I saw it firsthand in my twenties when I worked with youth in Franklin, Tennessee. Part of my responsibilities involved running student leadership programs, and I spent a lot of time on college campuses. I was consciously struck by the quality of this one group of young people; they seemed to be a little more rooted than everyone else and a lot more stable."),
        (lambda t: "Church of Jesus Christ of Latter-Day Saints" in t,
         "“Hi!” they would say. “I’m from the Latter-Day Saints community.”"),
        (lambda t: "What were the Mormons doing" in t and "bar mitzvahs" in t,
         "After this happened numerous times, I asked myself, What are they doing that we’re not doing? Now, I understood that Jewish tradition had bar mitzvahs to help young men emerge into adulthood, and classical traditions used formal apprenticeships and rites of passage. What were they doing to bring their young people into this all-encompassing, confident adulthood?"),
        (lambda t: "infused with a sense of priesthood" in t,
         "The first thing I noticed was the mindset they instill into every single young man: they infuse them with a sense of serious stewardship. As boys enter adolescence, they are given a sense that they bear real communal responsibility for the health and ongoing vitality of their community."),
        (lambda t: "thing they call seminary" in t,
         "Part of this is an intensive morning routine where, for an hour every day before school, young people gather to study, reflect, and master their foundational literature and ethics."),
        (lambda t: "two-year mission around the world to spread the Mormon gospel" in t,
         "After all of that comes the final step of initiation, probably one you’ve seen yourself—they send these young men on a two-year mission of service and discipline far from home, and you can imagine how formative that experience must be, what a defining space that creates, and how transformative it is. At the end of those two years, they’re officially welcomed home, back into the larger community, and they’re recognized for the journey they’ve completed."),
        (lambda t: "Christian tradition but from a whole range" in t and "God-honoring" in t,
         "This was the biggest, most comprehensive thing I had undertaken in my life. I read every book you’ve ever heard of in regard to manhood, drawing from historical, philosophical, and psychological traditions across cultures. I was determined to find out what it meant to be a man, what the role of manhood was, and how I could guide my son into that space of healthy, honorable masculinity."),
        (lambda t: "image bearer and son of God" in t,
         "Here’s my take: a man is a person endowed with agency, strength, and conscience, entrusted with the responsibility to create, cultivate, care, and defend for the common good and the flourishing of others."),
        (lambda t: "relates to God and who he is in the world" in t,
         "As we move forward with this definition of manhood and masculinity—how a man carries himself and who he is in the world—we will be operating between two guardrails, two things I think are crucial to keep in mind during the entire journey of being an intentional father: humility and service."),
        (lambda t: "Adam, the first man, failed" in t,
         "In classical archetypes of human failure, the downfall of men has consistently stemmed from two flaws: arrogance and passive neglect. A man wants to pursue selfish impulses, and when consequences strike, he refuses to accept responsibility. I want to see honorable men operating with authentic responsibility, living with integrity for the flourishing of others, embracing humility, and serving their community. If we can keep those things in mind, they provide a powerful framework for moving forward as an intentional father."),
        (lambda t: "conviction as a follower of Jesus" in t,
         "You see, ultimately, my conviction is that we are called to help our sons embody genuine moral greatness. My vision is not to produce men who conform to a superficial checklist that causes the world to say, “Now that’s a man!” My goal is to help our sons become people of profound integrity, empathy, and courage. That was my goal for my son when I started out on this path, and that’s still my goal."),
        (lambda t: "Because Jesus was the best man who ever lived" in t,
         "Why? Because we need ideals of character that elevate humanity. Look at the life of great moral leaders throughout history: their cause, their compassion, their courage, their love for other people, their willingness to confront hypocrisy, and their steadfast personal integrity. When you look at lives lived with that kind of moral clarity, you see what human beings are truly capable of. That’s what the vision of being an intentional father is—to help our sons achieve that standard of character."),
        (lambda t: "discipleship meeting" in t and "drank coffee" in t,
         "WHILE I WAS WALKING with my son, Nate, down this path, we had a daily ritual where we would sit down and have time together in the mornings. It was a dedicated mentorship conversation—we basically woke up early and drank coffee together."),
        (lambda t: "discipleship and formation pathway" in t,
         "Before we really dig in, I want to clarify briefly what The Intentional Father is and what it isn’t. It is a mentorship and formation pathway to walk through with your son, beginning in his adolescence and continuing through his entry into adulthood. It is both comprehensive and customizable, which means there may be a few things you choose to do a bit differently than I did, and there might be things you want to insert or remove."),
        (lambda t: "I’m not going to disciple your son for you" in t,
         "Here’s what it isn’t. I’m not going to mentor your son for you. I don’t have rigid daily scripts for you to read together, and I did this on purpose, because your son is not my son. He is unique. I’ll provide the frameworks and resources that were transformative for me, but it will still be up to you to grow as a father in knowing your son and discerning what he needs. And I want you to grow in self-awareness, wisdom, and personal conviction as you go along."),
        (lambda t: "No effort of love, discipleship" in t,
         "Those are difficult, complicated questions. But the most important thing in all of this is to love and pour into your son. No effort of love, mentorship, and development will ever be wasted in the life of your son, regardless of who he is or what he is wrestling with."),
        (lambda t: "God designed us to work in partnership" in t,
         "Don’t worry about stereotypes. I’m also not trying to produce a generation of domineering alpha males. But I do believe there are distinct differences between men and women, and that we are built to work in cooperative partnership with one another. A big part of our current crisis is that men don’t know who they need to be around women. I believe that fathers mentoring their sons in the way I am about to describe will benefit our culture."),
        (lambda t: "exercise of fasting and prayer" in t,
         "LET’S WRAP UP this chapter with our first two exercises, the first being an exercise of fasting and deliberate solitude. I want to encourage you to set aside at least twenty-four hours to fast, step away from daily distractions, and dedicate that time to deep reflection—cultivating wisdom, patience, and resolve, and centering your heart on pouring into your son along this path."),
        (lambda t: "God will speak to you about your own heart" in t and "spiritual covering" in t,
         "I believe if you take the time to do this, profound clarity will emerge about your own heart and about your son, giving you the focus and moral foundation to begin this journey and start this conversation with your son. Beginning with a dedicated time of quiet reflection and fasting will set a beautiful trajectory for what’s to come."),
        (lambda t: "spend some time in prayer and fasting" in t and "The Work" in t,
         "So, spend some time in quiet contemplation and fasting, watch The Work, do the hard inner work on your own character, and then you’ll be ready to jump into the next chapter."),
        (lambda t: "Do a twenty-four-hour fast and dedicate that time to prayer" in t,
         "Do a twenty-four-hour fast and dedicate that time to quiet reflection and journaling. Write down the things that come to mind about how you were fathered and the kind of father you would like to be. Commit the years ahead to living with intention, and clarify the values that will guide you. And watch the documentary The Work.")
    ],
    '14-chapter03.xhtml': [
        (lambda t: "what witness would God give" in t,
         "In The Funeral Exercise, you are encouraged to ask specific questions: If this is your funeral, what do you want your spouse to say about you? What would you like to hear your kids say? What would you hope your coworkers would say? And, ultimately, what honest verdict will your one and only life leave behind when measured against your highest values?"),
        (lambda t: "point people to Jesus" in t,
         "Most of us have a strong desire to send our sons into the world prepared, formed, and equipped. We want them to head out on their own with valuable resources and tools that will help them live the best life they can, be strong men of character, and inspire the people around them. This is true of just about every father out there, even those who on the surface might appear disinterested in their sons. The reality is that fathers have this desire for their children. It’s ingrained."),
        (lambda t: "Plan for Making Disciples" in t,
         "A Man with a Plan for Intentional Mentorship"),
        (lambda t: "practicing Christian dads take discipleship seriously" in t,
         "On the whole, intentional fathers take mentorship seriously, and most see the direct connection between their daily parenting and their child growing into a mature, principled adult. However, a small but significant minority express some uncertainty in this area."),
        (lambda t: "What do you want your son to know about God" in t,
         "What do you want your son to know about reality, about human nature, about himself, and about life? This is essentially a question about wisdom. What do you want him to know? There are foundational principles you’d like him to embrace, and it is vital that he has self-knowledge and quiet confidence as he steps out into the world. Start thinking through what you want him to know in big, overarching terms."),
        (lambda t: "Somebody is going to disciple your son" in t and "godly men" in t,
         "Somebody is going to mentor your son. Somebody is going to give your son a philosophy on how to live, and it’s either going to be you and a community of principled men (see exercise #3 below) or it’s going to be whatever catches his eye in the culture. Your son is going to become someone—he is going to grow up. His character will be formed by someone."),
        (lambda t: "followers of Jesus have a tremendous advantage" in t and "rich communities" in t,
         "The next exercise in preparing yourself and your son is to create an asset map. When we intentionally build a circle of trusted friends, mentors, and families, we have a tremendous advantage in developing young men. We have a strong relational network we can leverage to help raise our sons in purposeful ways."),
        (lambda t: "perhaps friends from college or other men in your church" in t,
         "Consider getting a group of other dads together, perhaps friends from college, colleagues, or neighbors, who have sons around the same age as yours—boys who are growing up together. Do this in community. When I started working through this with my own son, I found a small group of dads with sons Nate knew, and I sat down with them to present a vision for what I wanted to do for Nate.")
    ],
    '14-chapter04.xhtml': [
        (lambda t: "missionary. My grandfather was a very gifted teacher with a supernatural ministry" in t,
         "MY FATHER SPENT his defining years in a boarding school in India, enrolled there by his own father, who was an ideological zealot. My grandfather was a very gifted teacher and charismatic by all accounts, but he was not a good father. He came from a rigid mindset that believed personal devotion to an abstract cause mattered more than family or children, so in order to minimize distractions, he placed his kids in a boarding school, only seeing them a few times a year. As a result, my dad didn’t have the tools he needed to make the transition from adolescence to adulthood."),
        (lambda t: "Faith of My Father" in t and len(t) < 30,
         "Values of My Father"),
        (lambda t: "Practicing Christian dads are more likely" in t and "prioritized faith" in t,
         "When asked what their own fathers prioritized, many dads recall an emphasis on core ethical convictions as a foundational influence in their upbringing.")
    ],
    '16-chapter05.xhtml': [
        (lambda t: "holy fear" in t,
         "I tried to create a sense of mystery, a profound reverence around what he was about to enter into. And I also tried to create a sense of anticipation, excitement around some of the things that were going to go down. I kept it all very vague, but I wanted him to know that something was on the horizon, and it was a big deal."),
        (lambda t: "prayer of blessing over him, and a prayer of release" in t,
         "She then took him out to eat, and while they were together she shared some memories she felt were important between the two of them. She’d thought through her experience of parenting him up to that point, and she had prepared to share some key moments, places that indicated his character or personality. She then spoke heartfelt words of blessing over him, and an intentional release into emerging manhood."),
        (lambda t: "concepts of discipleship and formation" in t,
         "We parked at the beach near Coney Island and went out onto the shore and sat in a group. We began by giving the boys a vision of what it means to be a man, explaining to them the path of men through history. We discussed the concepts of mentorship and character formation. We told them there was an ancient pathway that all men of nobility walked, but this path had been lost."),
        (lambda t: "laid hands on them as a community of men, blessed them, and prayed" in t,
         "We gathered around them as a community of men, placed our hands on their shoulders, and affirmed them. We called out their strengths, challenged them to high standards, and celebrated the fact that a new journey was beginning."),
        (lambda t: "after I gave him these gifts, I prayed for him" in t,
         "Finally, after I gave him these gifts, I spoke a personal blessing over him. I told him how proud I was of him. It was a powerful, moving night."),
        (lambda t: "at church, or on top of a building" in t,
         "Place matters. Environments matter. Where is the best place for this ceremony to happen? Your house? Out in the woods? At a campsite after a hike? At the beach, in a quiet library, or on top of a building? On a special trip to a favorite or desired place? Make this a meaningful spot that your son will return to with joy."),
        (lambda t: "Prayers? Speeches? Laying on of hands?" in t,
         "What elements will your initiation include? Speeches? A formal blessing? Gift giving? Words of affirmation from other key men? The involvement of your father and other grandparents? Physical elements such as cutting hair or special clothes? Some sort of definitive moment such as running into the water, crossing a line, or facing a challenge?"),
        (lambda t: "helping disciple your son in the future" in t,
         "What men have played a significant role in your son’s life? Who would you like to play a role in helping mentor your son in the future? Which friends and family would be significant for both of you?")
    ],
    '16-chapter06.xhtml': [
        (lambda t: "where I’d prayed to the places I’d learned my values" in t,
         "So, I designed a pilgrimage. I decided to show Nate where the major lessons of my life had taken place, from the hills and vantage points where I’d reflected to the places I’d forged my values. I wanted to show him the key moments, key places, and key people in my life."),
        (lambda t: "Pentecostal youth revival" in t and "follow Jesus" in t,
         "Some of you may know my story—I experienced a profound personal awakening the weekend I turned seventeen. Prior to that, I had been cynical about morality and purpose; it seemed so boring and hypocritical to me. But then I met a group of the most dedicated, passionate young people I had ever encountered. Seeing their genuine conviction ignited something in me, and I was compelled toward a life of purpose, character, and service."),
        (lambda t: "great Christian men" in t and "4:00 a.m. praying man" in t,
         "During that time of my life, I started reading biographies about great historical leaders and thinkers, men whom I aspired to emulate. And as I read about their lives, I realized that almost all of them got up at 4:00 a.m. and spent a couple of hours in quiet reflection, journaling, and study, first thing, before they did anything else with their day. As I realized this about my heroes, I decided I was going to be a man of early morning discipline and contemplation."),
        (lambda t: "Anstey’s Hill" in t and "order to pray" in t,
         "There was a place I started going to in order to think and meditate called Anstey’s Hill. It was notorious when I was in high school. We would go camping up there, and the whole place was surrounded by mysterious local legends."),
        (lambda t: "worship, discuss the Bible, or pray together with their son" in t,
         "When fathers discuss activities they share with their sons, engaging in deep conversations about life, ethics, and guiding values ranks among the most impactful formative moments."),
        (lambda t: "“God,” I prayed, “give me a vision for the world.”" in t,
         "“Let me,” I resolved, “gain a true vision for the world.”"),
        (lambda t: "Billy Graham" in t and "God, give me the world" in t,
         "I was deeply inspired by the early Apollo astronauts who saw the first images of the earth rising over the desolate horizon of the moon. Seeing our fragile, blue planet hanging in the darkness of space evoked a profound reverence and an overwhelming sense of global responsibility."),
        (lambda t: "“God, give me cities.”" in t,
         "That perspective moved me so much that I decided I would find high places, look out over whatever horizons I could see, and resolve to make a meaningful difference in the cities of our world."),
        (lambda t: "where I used to pray in the mornings" in t,
         "All of this to say, I took Nate to that very place, the exact spot on Anstey’s Hill where I used to sit in quiet contemplation in the mornings."),
        (lambda t: "“I asked God to bring me to America,”" in t,
         "“I resolved to build my future in America,” I told Nate. “I sat here in the mornings, working through my fears, cultivating the courage to move to a new country and figure out how to build a life, raise a family, and make a difference.”"),
        (lambda t: "pray for New York, and I wanted to show him" in t,
         "Nate knows how much I love to get up on top of a building in our own city and contemplate New York, and I wanted to show him where that began."),
        (lambda t: "used by God to impact people’s lives" in t,
         "“I was a teenager,” I told him, “only a few years older than you, but I resolved in my heart that I would be a man of vision, that I would go forward into the world with a sense of purpose and a desire to positively impact people’s lives. That journey started right here where you’re standing.”"),
        (lambda t: "church where I became a Christian" in t,
         "After that, I took him back to the community hall where I had experienced that initial turning point—I wanted to help him understand where my passion came from. “Nate,” I said, “this is where my journey started. This is the place where everything changed for me.”"),
        (lambda t: "Uncle Darren and I used to come to pray" in t,
         "“Look, Nate, here’s the place where Uncle Darren and I used to meet in the mornings. Darren Whitehead, my best mate—this is where we would talk before school. We would sit on these steps and challenge each other, clarifying our ambitions and resolving to do something significant with our lives.”"),
        (lambda t: "sat on a pew, and again laid hands on him and prayed" in t,
         "I took Nate into that room, sat beside him, put my arm around his shoulder, and spoke deeply into his life. “Nate,” I said, “I believe in you, and I honor the lineage of integrity, courage, and perseverance passed down through our family.”"),
        (lambda t: "where I first met Jesus" in t,
         "I wanted him to see that this was where I first caught a vision for living deliberately, where everything changed for me, and where I formed the convictions that have propelled me all of these years. We shared an emotional, moving time there together."),
        (lambda t: "God-ordained moment" in t and "butcher shop" in t,
         "AFTER THAT, I had the privilege of taking Nate to the butcher shop where I started working at age fourteen. I dropped out of high school at sixteen and worked there as an apprentice until I was twenty. This was a defining landmark—Nate had heard all of my butcher stories, and I have the scars on my arms to back them up."),
        (lambda t: "vision in my heart of what God could do" in t and "Our church wouldn’t exist" in t,
         "“You’ve seen my whole life here, Nate. You’ve seen the places that have had the biggest impact on me. I want you to imagine me packing all of it up into two bags, taking everything I knew, everyone I loved, every experience I had, and standing here in this airport, about to move to another country with only the conviction in my heart of what was possible. I wanted to be a man willing to take calculated risks for what mattered. If I hadn’t done that, I wouldn’t have met your mother. We would never have moved to New York. You would never have been born. The community initiatives we built wouldn’t exist. Everything you know and love about your life wouldn’t exist.”"),
        (lambda t: "worship, discuss the Bible, or pray together with their daughter" in t,
         "When fathers discuss activities they share with their daughters, intentional conversations regarding character, ethics, and guiding values consistently foster the strongest emotional bonds.")
    ],
    '16-chapter07.xhtml': [
        (lambda t: "planting a church in New York" in t,
         "THERE WAS A TIME when we were founding a new community initiative in New York, but in order to save up money to afford living in that neighborhood, we moved out of the city center. I was getting tired of all of the driving back and forth, all of the miles. One time when Nate was with me, I apologized for dragging him around during his teenage years."),
        (lambda t: "We plant churches" in t,
         "“It’s okay, Dad. We’re Tysons. We build community. This is what our family does.”"),
        (lambda t: "church planting is what the Tyson family does" in t,
         "From his perspective, building community is what the Tyson family does. He’s grown up around it. We’ve been involved in it. And he has absorbed the idea that what comes with creating meaningful work is risk and sacrifice, paying the price, doing whatever it takes."),
        (lambda t: "even the church, but few people do so with their families" in t,
         "What are your values? Have you ever really taken the time to clarify what you and your family are all about? We obsess over values in the workplace and in our institutions, but few people do so with their families. I think it’s very, very important to be consciously aware of and seeking to cultivate our values in our children."),
        (lambda t: "for practicing Christian dads, around faith, honesty, and respect" in t,
         "Different people value different things. This goes for dads too. There is strong consensus among fathers, however, around the foundational values of respect, integrity, and honesty. When it comes to fathers of sons versus fathers of daughters, these core ethical priorities remain remarkably consistent."),
        (lambda t: "Scriptures speak to these values" in t,
         "Men sometimes use the strength they have to oppress other people; they draw on snippets and sound bites from random places as their source of philosophy, often without a historic or deep code of ethics. They are violent or passive, the two opposite sides of measured courage, and they are at times known by lack of restraint and given over to excess. Whether it be in the boardroom or the bedroom, men seem to have lost their way. Foolishness, excess, cowardice, and oppression are wreaking havoc and destroying men. But a recovery of the foundational values in men could heal society in a potent way. The classical wisdom literature speaks powerfully to these values, particularly as an exhortation to men."),
        (lambda t: "Listen, son of my womb! Listen, my son, the answer to my prayers!" in t,
         "Listen, my son! Pay close attention to instruction, child of my devotion and deepest hopes!"),
        (lambda t: "God given values of being conformed into the image of Jesus" in t,
         "I WANT TO BE CLEAR: imparting these values is not about fulfilling some sort of superficial cultural stereotype of what a real man looks like. This has nothing to do with posturing or bravado. The goal is to help young men cultivate universal moral virtues: wisdom, self-control, courage, and justice."),
        (lambda t: "no one has embodied these values like Jesus" in t,
         "Throughout history, remarkable figures have embodied these core values in action. Consider how they manifest in a life well-lived:"),
        (lambda t: "Wisdom. Jesus gave us the Sermon on the Mount" in t,
         "Wisdom. The capacity to see through illusions, offering a fresh vision of ethical love and human compassion. True wisdom cuts through superficial dogmas with insight that not only informs and inspires but sets the human mind free."),
        (lambda t: "Self-Control. Jesus showed remarkable self-restraint" in t,
         "Self-Control. The profound self-restraint required to master one’s appetites and emotions, remaining composed under fierce public provocation, and refusing to respond to malice in kind."),
        (lambda t: "Courage. Jesus boldly faced the cross" in t,
         "Courage. The steadfast resolve to confront difficult realities when others flee under pressure. True courage means remaining faithful to principles and protecting others even when facing severe personal cost."),
        (lambda t: "Justice. Jesus advocated for the oppressed" in t,
         "Justice. The active commitment to advocate for the vulnerable, create space for the marginalized, and fearlessly confront corruption and hypocrisy in the systems of one’s day, working to leave society fairer and more humane."),
        (lambda t: "raise up men with values like this, men like Jesus" in t,
         "Don’t you want to raise up young men with values like this? Can you imagine what would happen with your son if he were inspired and equipped to live like this in these challenging times?"),
        (lambda t: "unique to the ecosystem of men and are present in Christ" in t,
         "The following values represent foundational pillars of mature manhood. How will you model and embody these virtues for your son?"),
        (lambda t: "What have you learned about God?" in t,
         "What have you learned about human nature and your own character?")
    ],
    '18-chapter08.xhtml': [
        (lambda t: "apostle Paul reminds us" in t and "1 Corinthians 13:11" in t,
         "An ancient letter captured this pivotal transition with enduring clarity: “When I was a child, I talked like a child, I thought like a child, I reasoned like a child. When I became a man, I put the ways of childhood behind me.” This transition from childish self-absorption into mature adulthood is essential, and it must always be anchored in genuine empathy and love for others."),
        (lambda t: "morning meetings, I did a Bible teaching" in t,
         "Our core framework for walking through each of these shifts looked like this: during our morning meetings, we explored foundational readings and philosophical principles that illustrated whichever value we were discussing. We read classical wisdom literature, philosophical maxims, and moral essays. We read biographies of remarkable men and women, and on a weekly basis we watched a movie that embodied the shift we were exploring. We had long discussions about what that journey looked like and what its challenges were, and toward the end of our exploration into each shift I designed an experience and challenge to show Nate the joys and possibilities that come with moving from one to the other. I tried to end each one with a deep sense of reward, something that left him marked with positive feelings about what he would be shifting into."),
        (lambda t: "become more like Jesus Christ. Jesus left the ease" in t,
         "And remember, these aren’t just generic manhood shifts—these are the shifts that forge true moral greatness. We challenge our sons to move from ease to embracing worthwhile difficulty; from self-centeredness to living in service of others; from pursuing superficial celebrity to embracing quiet, diligent craftsmanship; from demanding total control to mastering what is within their power; and from chasing temporary thrills to building an enduring, generational contribution."),
        (lambda t: "serving team at our church" in t and "encounter with God" in t,
         "From self to others. I explained to Nate that he needed to realize life isn’t just about him and he needed to learn to live for other people, so I had him join a community volunteer crew. He chose the most demanding crew—the group that arrived early in the morning to haul equipment, set up the venue, and pack everything down late in the evening. And I did it with him to create solidarity between us. The two of us would arrive early to carry in the heavy gear. Let me tell you: there was no fanfare in this job, no glory. It was just setting the stage so others could gather and experience something meaningful. Nate stayed on that crew for a couple of years, and it was deeply transformative for him."),
        (lambda t: "story God was telling was way bigger" in t,
         "From the whole story to part of the story. I wanted Nate to begin to realize he lived in the middle of Manhattan and had a very privileged life, and the broader human story was far bigger than the streets he walked and the people he saw every day. I took him to different parts of the city and different parts of the world so he could be exposed to people who lived differently than he did, those with fewer resources, those who were underprivileged, those born into very dissimilar circumstances. I wanted him to realize life wasn’t about him just getting everything he wanted, that he was actually a tiny little part of a very big story. This is a difficult lesson to teach teenagers, who often can’t see beyond the boundaries of their own lives."),
        (lambda t: "We’re not God. We have to learn to surrender" in t,
         "From control to surrender. Life is a challenge, and things are going to come our way we can’t always control. Nate experienced this with the death of a pet. That might not sound like much to those of you who aren’t attached to animals, but we lost two dogs in pretty close succession, and it was really hard on him. He had to learn what it’s like to experience life as a challenge, and how to live through disappointment when things we can’t control come our way. There are giant forces at work in life, and we are not able to make everything go our way. We don't control external circumstances. We have to learn to accept reality with fortitude and focus our energy on how we choose to respond."),
        (lambda t: "lived for the kingdom of God, a life lived with eternity in mind" in t,
         "This experience marked him so deeply that there are still times when he’ll send me a text and at the end add #whats yourdash or #livingmydashwell. He caught the vision of a life bigger than himself, a life lived for something enduring, with a focus on leaving a lasting legacy."),
        (lambda t: "Make a list of resources you’d like to use for each shift: Bible passages" in t,
         "Make a list of resources you’d like to use for each shift: philosophy, biographies, literature, movies, real-world experiences, and anything else you can think of. Categorize them into the five different shifts. Plan to take at least a month or two on each shift."),
        (lambda t: "Scriptures to study:" in t,
         "Readings and case studies to explore:")
    ],
    '18-chapter09.xhtml': [
        (lambda t: "team called SA Church" in t,
         "I made it from our local league all the way up to the highest level of basketball I could play as a teenager in Australia, which was state basketball. I played for a team called SA League, a really strong team. We even made it all the way to the state grand final."),
        (lambda t: "didn’t become a Christian until I was almost seventeen" in t,
         "In order to tell this story, I should remind you that I didn’t experience that awakening toward purpose until I was almost seventeen, and growing up in Australia, the environment around me was often rough and combative."),
        (lambda t: "biblical proportions in my mind" in t,
         "It took on epic proportions in my mind, this potential fight, and at some point during the day the classic words were whispered: “3:30 behind the gym.”"),
        (lambda t: "show the mercy and grace of God" in t,
         "First exposure to LGBTQ perspectives. How you handle this topic with your child is vital. You’re either going to model basic human dignity, empathy, and respect, or you’re going to pass on prejudice and ignorance."),
        (lambda t: "call out the church when it gets this wrong? What does biblical justice look like?" in t,
         "First exposure to racism. We live in a divided world. You know it and I know it, but there’s something important about that first moment when your child recognizes it. Are you prepared to have that conversation? What do you do? And how do we call out institutions and leaders when they fail? What does true justice, human equality, and ethical courage look like in practice?"),
        (lambda t: "Doubts about faith" in t,
         "Wrestling with skepticism and personal convictions")
    ],
    '18-chapter10.xhtml': [
        (lambda t: "critiques leveled against the Christian men’s movement" in t,
         "My desire in that moment was not to give him a trite convincing answer or say something that would talk him into staying on track with me—I really wanted to get to the heart of his lack of motivation to keep going. And what came to my mind was the widespread critique leveled against modern men’s movements."),
        (lambda t: "Christian men’s movements are largely cliché" in t,
         "The pushback generally levels that the reason many men’s programs are largely cliché or ineffective is that they reduce virtue to merely avoiding trouble. A 'good boy'—what comes to mind? Often it’s someone defined purely by what he refrains from doing, spending his life trying not to mess up."),
        (lambda t: "common definition of what makes up a good man is actually not that inspiring. Christianity" in t,
         "What I’m trying to say is that our modern culture’s common definition of what makes up a good man is actually not that inspiring. Society hasn’t done a good job of presenting figures we can look at and think: Now that is what a great human being is. We’ve reduced virtue to timid, stressed compliance rather than living with courage, freedom, competence, and inner strength."),
        (lambda t: "how I pictured a Christian man" in t and "good Christian, a good man" in t,
         "I realized that this was how so many people picture a 'proper' young man. And more importantly, I had a breakthrough: Nate thought I was trying to turn him into a bland, compliant rule-follower."),
        (lambda t: "secular authors critique about Christian men" in t,
         "And, I kid you not, he went on to list many of the traits that critics frequently point out about passive masculinity. “Well, it’s about being responsible, not making trouble, listening to authority, doing your homework...” It was all passive!"),
        (lambda t: "teaching my son about how to be a Christian man" in t,
         "Over half of U.S. fathers say they have sought to offer their sons deliberate guidance on what it means to be a man, showing how deeply dads recognize the need for intentional direction."),
        (lambda t: "discipleship and development, specific advice" in t,
         "This is key. This is what men need. All of us need actual mentorship, coaching, and real-world development—specific skills, emotional fortitude, and practical wisdom that teach us how to be truly capable and effective in the world."),
        (lambda t: "vision of Christian manhood away from someone" in t,
         "Far too often, this is how we interact with the next generation of young people. We’re on the sidelines telling them to keep going, telling them they can do it, and they’re out there in the middle of their crazy lives thinking, I don’t know what to do. I don’t know how to keep going. This is why I decided to shift my vision away from mere passive compliance toward someone who is genuinely skillful, resilient, and honorable at living well as a man.")
    ],
    '18-chapter11.xhtml': [
        (lambda t: "not about efficiency; it’s about discipleship" in t,
         "Being a father is not about efficiency; it’s about mentorship. Being a father is not about time management; it’s about character formation. Being a father is not about checking things off; it’s about pouring into your son."),
        (lambda t: "Role #1: Disciple" in t,
         "Role #1: Student of Wisdom and Truth"),
        (lambda t: "discipleship wound in our churches" in t,
         "Not only is there a gaping father wound in our culture, but there is also a mentorship wound across our communities. If you were to gather a group of people and ask them to raise their hands if they felt they had been properly mentored into adulthood, you would see very few hands. If you followed that up by asking how many people would have loved to be mentored—to be deliberately guided in a way that helps them understand human nature, cultivate wisdom, and live with purpose—you’d see almost every hand go up. In fact, if someone tells you they were effectively mentored by an older guide, it feels rare and extraordinary."),
        (lambda t: "Being a Christian Disciple" in t,
         "Developing Moral and Intellectual Conviction"),
        (lambda t: "guidance on the following faith-related topics" in t,
         "Engaged fathers report that guiding their sons through key philosophical and worldview questions is one of their most essential responsibilities:"),
        (lambda t: "words in Luke 6:40" in t or "trained to become like Jesus" in t,
         "An ancient proverb reminds us: The student who is fully trained will reflect the character of the teacher. Being mentored is about being trained in wisdom, self-mastery, and moral courage."),
        (lambda t: "importance of being a good disciple" in t,
         "In order to help Nate understand the importance of being a disciplined thinker and student of life, I curated four core questions that we worked through together. Here they are."),
        (lambda t: "Who is God? What comes into our minds" in t,
         "What is my worldview and moral compass? What comes into our minds when we reflect on ethics, reality, and human dignity defines the trajectory of our lives. You’d be amazed at how much superficial, unexamined assumption floats around in the minds of young people who have simply absorbed whatever culture feeds them. Nate and I spent significant time examining worldview frameworks, exploring ethical philosophy, and digging into the question: What constitutes reality, truth, and a life of integrity?"),
        (lambda t: "What is the gospel? This is the second question" in t,
         "What is the good life? This was the second question we tackled. What does it mean for a human being to truly flourish? What principles lead to enduring fulfillment, meaningful relationships, and genuine peace of mind rather than shallow hedonism? I wanted to look my son in the eye and share my deepest convictions about what makes life rich, worthy, and good."),
        (lambda t: "What is the biblical story? The Bible can be a big" in t,
         "What is the human story? History is a vast, intricate journey, and there are so many chapters we can walk our teenagers through: the origins of human society, the struggle for freedom, the rise and fall of civilizations, the great philosophical revolutions, and the hard-won victories for human rights and democracy. I spent time helping Nate understand how our world came to be. My overarching goal was getting Nate to where he understood these things for himself. Not because I told him, but because he did his own reading, evaluated the evidence, and came to his own rational conclusions."),
        (lambda t: "How do I read the Bible? Nate and I went through" in t,
         "How do I engage great ideas and cultivate personal reflection? Nate and I used the acronym TIME: Truth, Insights, Mission, and Execution. This helped him analyze great texts, evaluate context, extract practical insights, clarify his personal mission, and apply principles to real dilemmas. I introduced him to the disciplines of journaling, solitude, and critical thinking so that he could make wise decisions, govern his emotions, and steer his life with purpose."),
        (lambda t: "Nate’s decision to get baptized" in t,
         "One of the highlights of this season was Nate’s formal commitment to personal values—his rite of passage into intellectual and moral maturity."),
        (lambda t: "follower of Jesus" in t and "understand the gospel" in t,
         "“Do you know what principles you stand for?” I asked Nate after we had worked through this material. “Do you understand what it takes to live an intentional life?”\n\n“Yes.”\n\n“Do you understand your responsibility in the human story? Are you committed to living with reason, integrity, and courage?”\n\n“Yes, I am.”\n\n“Do you want to live a life of consequence and service to others?”\n\n“Yeah, Dad, I do.”\n\n“Then are you ready to declare those commitments before our community?”\n\n“Yes, Dad; I’m excited to do this.”"),
        (lambda t: "walking with God and practicing the ways of Jesus" in t,
         None), # handeled in dialog above
        (lambda t: "Do you want to do God’s will" in t,
         None), # handeled in dialog above
        (lambda t: "Nate’s baptism was a beautiful moment" in t and "renounced Satan" in t,
         "That commitment ceremony was a beautiful milestone in our journey together. Standing before our community of mentors and family, hearing my son publicly articulate his core values and declare that he rejected malice, dishonesty, and cynicism was unforgettable. I cried like a baby. I still get choked up just thinking about it. We have a great photo of Nate after making his pledge, embraced by mentors who cheered him on."),
        (lambda t: "outsource the discipleship of your kids to their youth group" in t,
         "Please, don’t outsource the mentorship of your kids to outside programs or coaches. While mentors and programs can be valuable partners, you carry the primary responsibility to mentor your children, walk that path beside them, and equip them with the tools they need."),
        (lambda t: "right after being a disciple of Jesus" in t,
         "I consciously put this role right after mastering foundational values, because I knew Nate was in the middle of puberty and had entered a very dynamic phase of life. I wanted him to feel confident in his understanding of women and what it looked like to honor and respect them. We talked about the beauty and wonder of what a woman is, the importance of treating women with dignity, and the idea of being equal partners in life. I didn’t want him to take a cynical cultural view of women but to understand the privilege and joy of authentic partnership."),
        (lambda t: "57% of practicing Christians" in t,
         "While sex and dating should certainly not be the only ways women and men relate to one another, they are a hugely important aspect of teen and adult relationships. Yet just half of fathers say they’ve talked with their sons ages thirteen and older about these topics. Just one-third have discussed sexual consent and sexism with their teen or young-adult son."),
        (lambda t: "biblical accountability" in t and "sin to confession" in t,
         "We talked about authentic accountability and the importance of bringing our struggles into the open rather than hiding them in shame."),
        (lambda t: "Leadership Bible" in t,
         "Speaking of leadership, Nate and I also studied John Maxwell’s leadership principles and The 20 Most Important Minutes in a Candidate’s Life. We worked our way through many of John Maxwell’s books because they resonated with Nate a lot. He and I also dove into James Kouzes and Barry Posner’s book The Challenge of Leadership and their five exemplary behaviors of leadership. This whole leadership section was so rewarding."),
        (lambda t: "Dig into Scripture." in t,
         "Use your community. Use the media at your disposal. Read biographies. Dig into history and philosophy."),
        (lambda t: "Scriptures to study:" in t,
         "Readings to study:")
    ],
    '18-chapter12.xhtml': [
        (lambda t: "mystery it is" in t and "holy and hidden heart" in t,
         "Listen to your life. See it for the fathomless mystery it is. In the boredom and pain of it, no less than in the excitement and gladness: touch, taste, smell your way to the rich and hidden heart of it, because in the last analysis all moments are key moments, and life itself is a profound gift."),
        (lambda t: "who God has made and called them to be" in t,
         "Our goal as fathers is to help our sons discover who they uniquely are and what they are capable of becoming. We are not to make them in our image; we are to help them discover their own authentic voice and strengths."),
        (lambda t: "what his spiritual gifts were" in t,
         "I wanted him to have world-class insight into who he was, what his strengths were, what his innate aptitudes and talents were, and what roles he was suited for."),
        (lambda t: "God had sovereignly deposited areas of strength" in t,
         "One of the things I love about this program is that it has a specific version for young people, in which they modify the language and provide different insights, which was so encouraging because at the end of it, Nate was able to say, “Here are five things I’m really good at.” And it gave him areas of confidence and places to focus on building competence. It showed him how he was wired with distinct strengths, giving Nate the courage to step up and say, “I’m suited for that and I want to give it a try.”"),
        (lambda t: "Spiritual Gifts" in t and len(t) < 30,
         "Aptitudes and Strengths"),
        (lambda t: "formal spiritual gifts assessment" in t or "experience in the church" in t,
         "Comprehensive strengths assessments seem to mostly be reserved for adults; I personally know very few parents who have taken their kids through any kind of formal strengths assessment. But if we want our children to take ownership of their role in the community, as opposed to simply being passive consumers, this is essential."),
        (lambda t: "Christians will engage with the church" in t or "exploring innate aptitudes" in t,
         "I’ve heard a fair number of people dismiss the idea of exploring innate aptitudes, saying that assessments aren’t helpful or that it’s a pointless exercise. But I say the tests currently available create a helpful starting point for good conversations about how we engage with and contribute to our community."),
        (lambda t: "Nate enjoyed finding out what his spiritual gifts are" in t,
         "Nate enjoyed discovering what his primary strengths and aptitudes are, what they reveal about his temperament, and where he might find the greatest fulfillment in contributing to others. He liked discovering areas in which he was naturally gifted. We do our kids a disservice when we fail to help them understand how they are built to contribute and thrive."),
        (lambda t: "APEST Test is an Ephesians 4 test" in t,
         "Another helpful framework is the Five Archetypes assessment, which evaluates how a person contributes within an organization: pioneering new initiatives, visionary foresight, community outreach, mentorship and caregiving, or teaching and synthesis. It helps answer the questions: What role do I naturally play in a team or community? Where am I most effective? Launching new ventures? Strategic foresight? Building partnerships? Supporting and counseling people? Or educating and communicating?"),
        (lambda t: "plug into the mission of his local church" in t,
         "Knowing this has helped Nate think purposefully about how he can contribute effectively to meaningful community causes."),
        (lambda t: "discernment from a Christian perspective" in t,
         "We loved all of these various tests and exercises, and each one helped us learn so much about Nate and, more importantly, gave him insight into his own identity. But what felt like the crown jewel of all the tests was the Birkman Test, which has to be administered by a trained Birkman professional in order to get the right yield from it. It’s very comprehensive, with the goal of providing genuine vocational discernment and career guidance."),
        (lambda t: "larger kingdom of God" in t,
         "It helps answer questions such as, What part of our culture should you consider serving in? How do you find your place in contributing to society? What is your mission in the world? This was amazing because it gave Nate clear parameters to move forward with."),
        (lambda t: "God’s fingerprints and God’s design" in t,
         "One of the lies we tell our young people is that they can be whatever they want to be, but in reality we are limited by our talents, our temperaments, our personalities, and even our physical makeup. If you are four-foot-eleven, you’re going to struggle to make it to the NBA. That’s just a fact. So, how can we help our young people embrace their natural wiring and walk in the direction of their strengths? How can we help them understand their unique design and then move forward with those realities in mind?"),
        (lambda t: "what do you think God may be calling you to do" in t,
         "I began having informed conversations with Nate that weren’t just based on opinions. I could ask him questions like, “Nate, based on what you’ve learned about yourself, what sort of contribution do you feel called to make with your life? What sort of vocation aligns with your strengths? What education or training might be the right path to help you move toward this vocation?”")
    ],
    '18-chapter13.xhtml': [
        (lambda t: "learning more about God" in t,
         "After that comes college or vocational training, and we need to explain the temptations and joys of that time of life too. This phase is primarily about self-discovery—you have a bit of clarity about what direction you’d like to go, but you’re learning more about the world, learning more about humanity, and learning more about yourself."),
        (lambda t: "Hebrews 13:7 comes to mind" in t,
         "An ancient maxim comes to mind: “Remember your mentors and teachers who imparted wisdom to you. Consider the outcome of their way of life and emulate their character and integrity.”")
    ],
    '20-chapter14.xhtml': [
        (lambda t: "I was their youth pastor and had been discipling them" in t,
         "I thought of a specific handful of guys whom I had mentored through high school for five or six years. I watched them go on to college and noticed how challenging that transition was."),
        (lambda t: "Adventures in Missions" in t,
         "Adventures in Service was an organization that, for over two decades, has been sending young people around the world to serve, grow, and engage with diverse cultures."),
        (lambda t: "I am a pastor, and not at a church that teaches the prosperity gospel" in t,
         "I have worked primarily in community leadership and non-profit initiatives. Our vocation isn’t known for large financial windfalls, and New York City is an expensive place to raise a family. But with discipline and planning, this trip came together. And looking back, I have zero regrets at the sacrifices to make it happen."),
        (lambda t: "doesn’t want to walk with God" in t and "what God can do" in t,
         "“What if my son goes off the rails sometimes during these years? What if he rejects the values we’ve worked so hard to instill?” Listen, these things happen. There are countless gap year programs focused on practical skills, service, and travel. You will be amazed at what a year of new perspective can do for a young person’s maturity, especially when they can get away from familiar routines and see the world through fresh eyes.")
    ],
    '20-chapter15.xhtml': [
        (lambda t: "God blessed them and said to them" in t and "Be fruitful" in t,
         "From the earliest traditions of human storytelling, elders spoke formal blessings over the young before sending them into the world to take on responsibility. Notice this fundamental principle: authentic affirmation and blessing must precede authority."),
        (lambda t: "Jacob chased his father’s blessing" in t and "Bible shows us" in t,
         "Just like classical archetypes of sons longing for paternal approval, your son will hunger for your blessing if you don’t grant it to him intentionally. He’ll enter adulthood seeking validation from all the wrong places—from superficial relationships, relentless status seeking, peer approval, or material excess. Because that validation isn't anchored in genuine respect, it leaves an empty void. Your son has an innate, psychological need for you to look him in the eye and say, “I am proud of you; you are a man of character and strength.”"),
        (lambda t: "ENDING OF MATTHEW’S GOSPEL" in t and "make disciples of all nations" in t,
         "CONSIDER THE PIVOTAL MOMENT when a great mentor prepares to release his students into the world. The best endings aren't filled with threats, panic, or endless anxious warnings. They are marked by profound affirmation and release."),
        (lambda t: "vicinity of Bethany, he lifted up his hands and blessed them" in t,
         "The mentor gathers those he has prepared, lifts his hands, and speaks words of confidence and blessing over them. Empowered by that affirmation, the students step out into the world not in fear or hesitation, but with great joy, ready to shoulder the challenges ahead."),
        (lambda t: "disciples of Christ in Acts operating from Jesus’s blessing" in t,
         "Because of that release, young people learn to operate from a foundation of blessing rather than constantly chasing after it. So many men in our culture spend their entire lives frantically striving for their father’s approval—trying to amass wealth, status, or acclaim simply to finally receive a nod of validation from their dad."),
        (lambda t: "connects with God is through worship" in t,
         "And because Nate has always drawn deep inspiration and solace from music, we gathered together and played powerful songs of resilience, brotherhood, and hope, celebrating the unbreakable bond we share."),
        (lambda t: "picture of the blessing our heavenly Father offers us in Christ" in t,
         "My deepest hope as you do this is that your deliberate blessing provides your son with an unshakable foundation of respect and affirmation—a milestone marking the moment he stepped into adulthood knowing he lives not striving for validation, but grounded in it.")
    ],
    '20-chapter16.xhtml': [
        (lambda t: "discipleship of young people becomes a normal thing in the Christian tradition" in t,
         "It is part of my life vision that this kind of intentional mentorship of young people becomes a standard in our culture. Fathers and mentors stepping up, guiding young men, walking beside them, and helping them navigate the challenges, pitfalls, opportunities, and responsibilities that come with transitioning into adulthood."),
        (lambda t: "lead to God doing something significant in this next generation" in t,
         "Engaging in this kind of intentional path will impact more people than you and the young person you’re walking alongside—you are going to inspire people around you to pick up their game too. And the young people who see you going through this with your son will want something greater. They’ll want to be part of something like this. Your involvement will inspire communities everywhere, creating a wave of intentional fathers and mentors that raises up a formidable next generation of men."),
        (lambda t: "getting up early to seek God" in t,
         "What if I can’t meet every morning? I get it. Everyone’s schedule is different. Sometimes I had to travel, and we often did our morning time on video calls. The key to the whole thing is consistency, and I tried to help him see this. I would often tell him, “Nate, before you were born, I was getting up early to reflect, study, and center my mind, and when you leave my home, I will still use this time to cultivate purpose and wisdom. I want you to know that I’m inviting you into this sacred daily discipline, and I hope you establish this habit in your own life.”"),
        (lambda t: "150 hours of explicitly Christian content" in t,
         "Research shows that the typical young person is exposed to three thousand hours of uncurated media and algorithm-driven content a year, compared to a tiny fraction of that time spent in deep, deliberate mentorship with parents. Who do you think is shaping their worldview? Who is having the primary formative influence?"),
        (lambda t: "close out this book by praying for you" in t,
         "I want to close out this book by speaking a direct charge and blessing over you as a father. Can I do that? I don’t know where you are as you’re reading this, but wherever you are, pause for just a moment, take a deep breath, and let these words sink in."),
        (lambda t: "Let me pray for you" in t,
         "Let me offer this charge to you:"),
        (lambda t: "Father, I come into your presence" in t or "throne room of God" in t,
         "To every father, mentor, and guardian reading these words: May you recognize the profound dignity, weight, and joy of the task before you. May you cultivate the patience, wisdom, and steadfast courage to lead your son with honor."),
        (lambda t: "Lord God, release the power of the Holy Spirit" in t,
         "May your imagination be stirred, fanning into flame the unique strengths within you, drawing on every lesson from your own journey to pour into the next generation."),
        (lambda t: "generational drama" in t and "blessing would flow" in t,
         "I charge you to stand firm against cynicism and distraction. May you break any generational pain, neglect, or apathy that came before you, establishing a new legacy of emotional courage, presence, and unwavering support."),
        (lambda t: "keys to our sons’ hearts" in t,
         "May you discover the key to your son's heart—listening before speaking, leading by living example rather than empty demands, and standing with him as he tests his strength and discovers his unique place in the world. Turn your heart toward your son, and earn the privilege of having his heart turned toward you. May you send into the world a person of character, consequence, and compassion who will leave humanity richer for his presence."),
        (lambda t: "In Jesus’s name, Amen" in t,
         "Go forward with purpose, integrity, and courage. You have what it takes to be an intentional father.")
    ],
    '22-abouttheresearch.xhtml': [
        (lambda t: "oversample of 612 practicing Christians" in t,
         "RESEARCH FOR THE INTENTIONAL FATHER was designed and analyzed by Barna Group. Participants in the survey were U.S. men ages eighteen and older who have at least one biological child, adopted child, or stepchild between the ages of ten and twenty-five. The project was conducted online March 27, 2020, to May 7, 2020, and included representative surveys among 1,058 total respondents across diverse cultural backgrounds.")
    ],
    '24-author.xhtml': [
        (lambda t: "JON TYSON is a church planter and the lead pastor" in t,
         "JON TYSON is an author, speaker, and community leader living in New York City, where he has lived for the last sixteen years with his wife and family. He is the creator of The Primal Path, an intensive fatherhood and mentorship initiative designed to guide young men into lives of purpose, character, and integrity. He is the author of several books. For more insight into becoming an intentional father, visit primalpath.co.")
    ]
}

def clean_pagebreaks_and_folios(soup):
    for span in list(soup.find_all(attrs={"epub:type": "pagebreak"})):
        span.decompose()
    for span in list(soup.find_all("span", id=re.compile(r"^page\d+"))):
        span.decompose()
    for p in list(soup.find_all("p", class_=re.compile(r"toc-marker"))):
        if re.match(r"^[\s\d—\-–\.]+$", p.get_text()):
            p.decompose()

def run():
    print("=== 1. Fresh copy from unpacked to unpacked_secular ===")
    retained_source_files = [f for f in os.listdir(SRC_TEXT_DIR) if f.endswith('.xhtml') and f not in DROPPED_FILES]
    for fname in retained_source_files:
        shutil.copyfile(os.path.join(SRC_TEXT_DIR, fname), os.path.join(DST_TEXT_DIR, fname))

    for df in DROPPED_FILES:
        target = os.path.join(DST_TEXT_DIR, df)
        if os.path.exists(target):
            os.remove(target)

    print("=== 2. Applying BeautifulSoup tag replacements ===")
    replaced_count = 0
    for fname in sorted(retained_source_files):
        fpath = os.path.join(DST_TEXT_DIR, fname)
        soup = bs4.BeautifulSoup(open(fpath, encoding='utf-8').read(), 'html.parser')
        clean_pagebreaks_and_folios(soup)

        file_rules = RULES.get(fname, [])
        tags_to_process = list(soup.find_all(['p', 'h1', 'h2', 'h3', 'blockquote', 'li']))

        for tag in tags_to_process:
            txt = ' '.join(tag.get_text().split())
            for pred_fn, replacement in file_rules:
                if pred_fn(txt):
                    if replacement is None:
                        tag.decompose()
                    else:
                        tag.clear()
                        tag.append(replacement)
                    replaced_count += 1
                    break

        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(str(soup))

    print(f"Applied {replaced_count} BeautifulSoup paragraph replacements.")

    print("=== 3. Audit for remaining religious / faith terms ===")
    remaining = []
    for fname in sorted(retained_source_files):
        if fname == 'toc.xhtml': continue
        fpath = os.path.join(DST_TEXT_DIR, fname)
        soup = bs4.BeautifulSoup(open(fpath, encoding='utf-8').read(), 'html.parser')
        for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'blockquote', 'li']):
            txt = ' '.join(p.get_text().split())
            if AUDIT_REGEX.search(txt):
                remaining.append((fname, txt))

    print(f"Total remaining matches after BS4 replacement: {len(remaining)}")
    for fn, rm in remaining:
        print(f"  [{fn}] {rm[:110]}")

if __name__ == '__main__':
    run()
