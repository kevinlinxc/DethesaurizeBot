import praw
import nltk

reddit = praw.Reddit(user_agent="LMGTFY (by /u/USERNAME)",
                     client_id="rvIGal4kwmJedg", client_secret="oWWZzluAWEmda0gemxpn2xWpk7s",
                     username="Kevinrocks7777", password="Andjelkovic7")

def check_comment(c):
    return True
    text = c.body
    tokens = text.split()
    if "!dethesaurizethis".lower() in tokens or "!dethesaurizethisbot".lower() in tokens:
        return True
    return False


for comment in reddit.subreddit("iama").stream.comments():
    if check_comment(comment):
        dethesaurized = dethesaurize(comment)





# for comment in reddit.subreddit("ffrecordkeeper").stream.comments(skip_existing=True):
#     print(comment)