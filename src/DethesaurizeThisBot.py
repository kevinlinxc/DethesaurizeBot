import praw
import nltk
import json
import readability
from nltk.corpus import wordnet as wn
from nltk.tokenize.treebank import TreebankWordDetokenizer

#Global variables used for
count = 0
limit = 3
GunningFog = 0.3
DaleChall = 0.4
Kincaid = 0.3

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
    return True
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


#Accepts a string and uses various weighted readability metrics to estimate the string's complexity/simplicity
def simplicity(string):
    tokens = nltk.word_tokenize(string)
    DC = readability.getmeasures(tokens)['readability grades']['DaleChallIndex']
    GF = readability.getmeasures(tokens)['readability grades']['GunningFogIndex']
    K = readability.getmeasures(tokens)['readability grades']['Coleman-Liau']
    #print(f'DC: {DC}, GF: {GF}, K: {K}')
    return DaleChall*DC + GunningFog*GF + Kincaid*K


# Main meat of this program, dethesaurizing a string by replacing hard words with easier ones
def dethesaurize(string):
    initialreadability = simplicity(string)
    print(f'Starting readability: {initialreadability}')
    tokens = nltk.word_tokenize(string)
    tokenscopy = tokens
    #print(f'Tokens: {tokens}')
    tags = nltk.pos_tag(tokens)
    for index, (word,tag) in enumerate(tags):
        if len(word) >= 5: #somewhat arbitrary
            replacement = simplestSynonym(tokenscopy, word, tag, index, initialreadability)
            tokens[index] = replacement
    return TreebankWordDetokenizer().detokenize(tokens)


#helper method for dethesaurize to reduce clutter. Finds the simplest synonym for a given word, checking that the word
#still fits in the sentence (same tag) and that it decreases reability score (better)
def simplestSynonym(tokens, word, tag, index, initialreadability):
    bestword = word
    bestreadability = initialreadability
    synonyms = get_synonyms(word, tag)
    for synonym in synonyms:
        tokens[index] = synonym
        tags = nltk.pos_tag(tokens)
        newstring = TreebankWordDetokenizer().detokenize(tokens)
        newsimplicity = simplicity(newstring)
        #print(f'If we replaced {word} with {synonym} the simplicity would be {newsimplicity}')
        if tags[index][1] == tag and newsimplicity < bestreadability:
            bestword = synonym
            bestreadability = newsimplicity
    return bestword

print(dethesaurize('I refuse to pick up refuse.\n'))
# Read all comments and check if
for comment in reddit.subreddit("all").stream.comments(skip_existing=True):
    if count >= limit:
        break
    print(f'Comment #{count}')
    count += 1
    print(f'Original comment: {comment.body}')
    body = ''
    title = ''
    if check_comment(comment):
        parent = comment.parent()
        #if the parent is a submission (post)
        if isinstance(parent, praw.models.Submission):
            submission = True
            # Dethesaurize the title and the body, and if one doesn't exist, don't include it.
            #If neither exist, reply with an error
            body = parent.selftext
            title = parent.title
            print(f'Parent is a submission with title: {title} and body: {body}')
            if body != '':
                body = f'Body: {dethesaurize(body)}\n'
            if title != '':
                title = f'Title: {dethesaurize(title)}\n'
            output = title + body
            if output == '':
                output = 'At the time of request, I don\'t see anything to dethesaurize.'
            print(f'Output: {output}')
            finalreadability = simplicity(output)
            print(f'Final readability: {finalreadability}')
        #if the parent is a comment
        elif isinstance(parent, praw.models.Comment):
            submission = False
            body = parent.body
            print(f'Parent is a comment with body: {body}')
            output = dethesaurize(body)
            finalreadability = simplicity(output)
            print(f'Output: {output}')
            print(f'Final readability: {finalreadability}')
        else:
            print("Looks like the parent isn't a comment or a submission")
            break

# for comment in reddit.subreddit("ffrecordkeeper").stream.comments(skip_existing=True):
#     print(comment)
