import language_tool_python
from helpers import dethesaurize, get_synonyms
import nltk

def checkgrammar(message):
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(message)
    print(matches)
    message = language_tool_python.utils.correct(message,matches)
    return message

def checkdethesaurization(message):
    new = dethesaurize(message)
    return new

tokens = nltk.word_tokenize("I am experiencing vicissitudes")
tags = nltk.pos_tag(tokens)
print(tags)

print([i for i in get_synonyms("vicissitudes",'NNS')])
#print(checkdethesaurization("I am experiencing vicissitudes"))