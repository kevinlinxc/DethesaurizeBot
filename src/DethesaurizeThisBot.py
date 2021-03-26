import praw
import json
import language_tool_python
from helpers import check_comment,  simplicity, dethesaurize
import nltk

#Global variables
count = 0
limit = 2

OutputToReddit = True
tool = language_tool_python.LanguageTool('en-US')
# Open config file if running locally
with open('config.json') as config_file:
    config = json.load(config_file)['keys']
# Open environment variables if running on Heroku
# config = os.environ

# Sign into Reddit using API Key
reddit = praw.Reddit(user_agent="DethesaurizeBot (by /u/Kevinrocks7777). Call using !dethesaurizethis or "
                                "!dethesaurizethisbot",
                     client_id=config['client_id'],
                     client_secret=config['client_secret'],
                     username=config['username'],
                     password=config['password'])

print("Reddit initialized")

# If !dethesaurizethis is detected, dethesaurize the parent comment and reply to the !
# Default to dethesaurizing body only. If there's a title and no body, dethesaurize the title
# If the title is specifically requested, it will be dethesaurized.
for comment in reddit.subreddit("all").stream.comments(skip_existing=True):
    bodyOnly = True #default
    titleOnly = False

    body = ''
    title = ''
    outputbody = ''
    outputtitle = ''
    output = ''

    if check_comment(comment):#If comment contains !dethesaurizethis
        print(f'Comment #{count}') #print out the comment if its looking for us
        count += 1

        print(f'Original comment: {comment.body}')
        parent = comment.parent()

        #if the parent is a submission (post)
        if isinstance(parent, praw.models.Submission):
            submission = True
            #Check if the orginal comment wants the title to be dethesaurized
            if 'title' in comment.body.lower():
                titleOnly = True
                bodyOnly = False
            # Dethesaurize the body or the title if the title was requested
            #If neither exist, reply with an error
            body = parent.selftext
            title = parent.title
            print(f'Parent is a submission with title: {title} and body: {body}')
            if body == '' and title != '':#If the title isnt requested, but it exists and body doesn't, do title
                titleOnly = True
            if body != '' and bodyOnly:
                outputbody = f'{dethesaurize(body)}\n'
            if title != '' and titleOnly:
                outputtitle = f'{dethesaurize(title)}\n'
            output = outputtitle + outputbody
            #if neither body or title have anything, or if title was requested but it was empty
            if output == '':
                output = 'At the time of request, I don\'t see anything to dethesaurize.'
            print(f'Dethesaurized: {output}')
            matches = tool.check(output)
            tool.correct(output)
            print(f'Grammar checked: {output}')
            finalreadability = simplicity(output)
            print(f'Final readability: {finalreadability}')
            if OutputToReddit:
                comment.reply(output)
        #if the parent is a comment
        elif isinstance(parent, praw.models.Comment):
            submission = False
            body = parent.body
            print(f'Parent is a comment with body: {body}')
            output = dethesaurize(body)
            if output == '':
                output = 'At the time of request, I don\'t see anything to dethesaurize.'
            print(f'Dethesaurized: {output}')
            matches = tool.check(output)
            tool.correct(output)
            print(f'Grammar checked: {output}')
            finalreadability = simplicity(output)
            print(f'Final readability: {finalreadability}')
            if OutputToReddit:
                comment.reply(output)
        else:
            print("Looks like the parent isn't a comment or a submission")
            break

# for comment in reddit.subreddit("ffrecordkeeper").stream.comments(skip_existing=True):
#     print(comment)
