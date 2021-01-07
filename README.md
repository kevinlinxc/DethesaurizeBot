# DethesaurizeBot
A work-in-progress Reddit bot that can be summoned to simplify ("Dethesaurize") sentences.

Summon by commenting !dethesaurizethis or !dethesaurizethisbot under a comment or post while the bot is running (will work on keeping bot up after functionality).

DethesaurizeBot makes use of the **Python Reddit API Wrapper (PRAW)** to access Reddit and the **Natural Language Toolkit (NLTK)** to simplify sentences.

A combination of readability metrics are used to determine the initial difficulty of a passage, and then an algorithm I developed replaces harder words with simpler synonyms while trying to maintain correct semantics and Parts Of Speech.


The repository has some files that were used in trying to set up Heroku hosting, but ultimately it seems very challenging to host this bot with Heroku because of Heroku's lack of Java, which language_tool relies on.
