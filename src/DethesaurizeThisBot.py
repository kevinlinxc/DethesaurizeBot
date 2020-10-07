import praw
import nltk
import json
import readability
import re
from nltk.corpus import wordnet as wn
import language_tool_python

#Global variables
count = 0
limit = 2
GunningFog = 0.3
DaleChall = 0.4
Cole = 0.3
OutputToReddit = True
tool = language_tool_python.LanguageTool('en-US')
# Open config file, used to hide username and password from git
with open('config.json') as config_file:
    config = json.load(config_file)

# Sign into Reddit using API Key
reddit = praw.Reddit(user_agent="DethesaurizeBot (by /u/Kevinrocks7777). Call using !dethesaurizethis or "
                                "!dethesaurizethisbot",
                     client_id=config['keys']['client_id'],
                     client_secret=config['keys']['client_secret'],
                     username=config['keys']['username'],
                     password=config['keys']['password'])


# Function that checks if the a comment is requesting the bot to come. Return True at the top for testing
def check_comment(c):
    text = c.body
    tokens = text.split()
    if "!dethesaurizethis" in tokens[0].lower() or "!dethesaurizethisbot" in tokens[0].lower():
        return True
    else:
        return False


#Gets synonyms based not only on the word but also part of speech. Courtesy of DarrylG on SO
def get_synonyms(word, pos):
    ' Gets word synonyms for part of speech '
    for synset in wn.synsets(word, pos=pos_to_wordnet_pos(pos)):
        for lemma in synset.lemmas():
            yield lemma.name()


#Converts nltk pos to wordnet pos. Courtesy of DarrylG on SO
def pos_to_wordnet_pos(penntag, returnNone=False):
    ' Mapping from POS tag word wordnet pos tag '
    morphy_tag = {'NN': wn.NOUN, 'JJ': wn.ADJ,
                  'VB': wn.VERB, 'RB': wn.ADV}
    try:
        return morphy_tag[penntag[:2]]
    except:
        return None if returnNone else ''

#https://stackoverflow.com/a/34682849/11741232
def untokenize(words):
    """
    Untokenizing a text undoes the tokenizing operation, restoring
    punctuation and spaces to the places that people expect them to be.
    Ideally, `untokenize(tokenize(text))` should be identical to `text`,
    except for line breaks.
    """
    text = ' '.join(words)
    step1 = text.replace("`` ", '"').replace(" ''", '"').replace('. . .',  '...')
    step2 = step1.replace(" ( ", " (").replace(" ) ", ") ")
    step3 = re.sub(r' ([.,:;?!%]+)([ \'"`])', r"\1\2", step2)
    step4 = re.sub(r' ([.,:;?!%]+)$', r"\1", step3)
    step5 = step4.replace(" '", "'").replace(" n't", "n't").replace(
         "can not", "cannot")
    step6 = step5.replace(" ` ", " '")
    return step6.strip()

#Accepts a string and uses various weighted readability metrics to estimate the string's complexity/simplicity
def simplicity(string):
    tokens = nltk.word_tokenize(string)
    DC = readability.getmeasures(tokens)['readability grades']['DaleChallIndex']
    GF = readability.getmeasures(tokens)['readability grades']['GunningFogIndex']
    C = readability.getmeasures(tokens)['readability grades']['Coleman-Liau']
    #print(f'DC: {DC}, GF: {GF}, K: {K}')
    return DaleChall * DC + GunningFog * GF + Cole * C


# Main meat of this program, dethesaurizing a string by replacing hard words with easier ones
def dethesaurize(string):
    initialreadability = simplicity(string)
    print(f'Starting readability: {initialreadability}')
    tokens = nltk.word_tokenize(string)
    tokenscopy = tokens
    #print(f'Tokens: {tokens}')
    tags = nltk.pos_tag(tokens)
    for index, (word, tag) in enumerate(tags):
        if len(word) >= 5:  #somewhat arbitrary
            replacement = simplestSynonym(tokenscopy, word, tag, index, initialreadability)
            tokens[index] = replacement
    return untokenize(tokens)


#helper method for dethesaurize to reduce clutter. Finds the simplest synonym for a given word, checking that the word
#still fits in the sentence (same tag) and that it decreases reability score (better)
def simplestSynonym(tokens, word, tag, index, initialreadability):
    bestword = word
    bestreadability = initialreadability
    synonyms = get_synonyms(word, tag)
    for synonym in synonyms:
        tokens[index] = synonym
        tags = nltk.pos_tag(tokens)
        newstring = untokenize(tokens)
        newsimplicity = simplicity(newstring)
        #print(f'If we replaced {word} with {synonym} the simplicity would be {newsimplicity}')
        if tags[index][1] == tag and newsimplicity < bestreadability:
            bestword = synonym
            bestreadability = newsimplicity
    return bestword


# If !dethesaurizethis is detected, dethesaurize the parent comment and reply to the !
# Default to dethesaurizing body only. If there's a title and no body, dethesaurize the title
# If the title is specifically requested, it will be dethesaurized.
for comment in reddit.subreddit("all").stream.comments(skip_existing=True):
    bodyOnly = True #default
    titleOnly = False
    #Limit number of comments for testing
    # if count >= limit:
    #     break


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
