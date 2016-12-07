# Stuff inherited from twitter-reading assignment
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

## Reading database keys
import json
with open('keys_twitter.json', 'r') as f:
   account_info = json.loads(f.read())
   vault = account_info['vault']
   keys = account_info['twitter']

twitter_key = keys['key']
twitter_secret = keys['secret']

client = BackendApplicationClient(client_id=twitter_key)
oauth = OAuth2Session(client=client)
token = oauth.fetch_token(token_url='https://api.twitter.com/oauth2/token',
                          client_id=twitter_key,
                          client_secret=twitter_secret)
base_url = 'https://api.twitter.com/1.1/'
page = 'search/tweets.json'

# Reads all tweets up to a limit (default 30000)
# and returns the array
# query should be the query string to be searched for (will go into the "?q=" part)
def getTweets(url, query, limit = 30000):
  initialQuery = url + '?q=' + query +'&count=100'
  response = oauth.get(initialQuery)
  results = json.loads(response.content.decode('utf-8'))
  tweets = results['statuses']
  while len(tweets) <= limit:
    if not ('next_results' in results['search_metadata']):
      break
    next_search = base_url + page + results['search_metadata']['next_results']
    response = oauth.get(next_search)
    results = json.loads(response.content.decode('utf-8'))
    tweets.extend(results['statuses'])
  return tweets

from sqlalchemy import *

engineUrl = ('mysql+mysqlconnector://' + vault['username'] +
             ':' + vault['password'] +
             '@' + vault['server'] +
             '/' + vault['schema'])

# Establishing a specific database connection
engine = create_engine(engineUrl, echo = True)

metadata = MetaData()
dbusers = Table('tw_users', metadata,
   Column('id', BigInteger, primary_key = True),
   Column('screen_name', String(140)),
   Column('name', String(140))
)
dbtweets = Table('tw_tweets', metadata,
   Column('id', BigInteger, primary_key = True),
   Column('text', String(150), nullable = False),
   Column('created', DateTime(timezone = True), nullable = False),
   Column('user', BigInteger, ForeignKey('tw_users.id'), nullable = False)
)
dbmentions = Table('tw_mentions', metadata,
   Column('tweet_id', BigInteger, ForeignKey('tw_tweets.id'), primary_key = True),
   Column('user_id', BigInteger, ForeignKey('tw_users.id'), primary_key = True)
)
dbhashtags = Table('tw_hashtags', metadata,
   Column('tweet_id', BigInteger, ForeignKey('tw_tweets.id'), primary_key = True),
   Column('hashtag', String(140), primary_key = True)
)
# Create these tables if they do not exist
metadata.create_all(engine)

hanover = getTweets(base_url+page, 'from:HanoverPanthers')
chicago= getTweets(base_url+page, 'from:UofCBasketball')

conn = engine.connect()
from datetime import datetime
time_format = '%a %b %d %H:%M:%S +0000 %Y'

# The following 4 methods obtain lists of values that we would
# want to insert into the database, starting from a list of tweets.
#
# Returns a list of all users (possibly with duplicates)
def getAllUsers(tweets):
   allUsers = ([ tweet['user'] for tweet in tweets ] +
               [  user
                  for tweet in tweets
                  for user in tweet['entities']['user_mentions']
               ])
   return [
      {
         'id': user['id'],
         'screen_name': user['screen_name'],
         'name': user['name']
      }
      for user in allUsers
   ]

# Returns a list of mentions ready to go in database
def getAllMentions(tweets):
   return [
      { 'tweet_id': tweet['id'], 'user_id': user['id'] }
      for tweet in tweets
      for user in tweet['entities']['user_mentions']
   ]

# Returns tweet-hashtag pairs
def getAllHashtags(tweets):
   return [
      { 'tweet_id': tweet['id'], 'hashtag': tag['text'] }
      for tweet in tweets
      for tag in tweet['entities']['hashtags']
   ]

# Returns simplified tweet entries
def getSimpleTweets(tweets):
   return [
      {
         'id': tweet['id'],
         'created': datetime.strptime(tweet['created_at'], time_format),
         'text': tweet['text'],
         'user': tweet['user']['id']
      }
      for tweet in tweets
   ]

## Processes the tweets
def processTweets(tweets):
   # Add users:
   conn.execute(dbusers.insert().prefix_with('IGNORE'), getAllUsers(tweets))
   # Add all tweets
   conn.execute(dbtweets.insert().prefix_with('IGNORE'), getSimpleTweets(tweets))
   # Add mentions
   conn.execute(dbmentions.insert().prefix_with('IGNORE'), getAllMentions(tweets))
   # Add hashtags
   conn.execute(dbhashtags.insert().prefix_with('IGNORE'), getAllHashtags(tweets))

processTweets(hanover)
processTweets(chicago)

# Add your answers here
#1 .group_by('tw_tweets.id')
tag_counts = select([dbtweets.c.id, dbusers.c.name, 
                     func.count(dbhashtags.c.hashtag).label('no_hashtags')
                    ]).select_from(dbusers.join(dbtweets).outerjoin(dbhashtags)).group_by('tw_tweets.id')
results1 = conn.execute(tag_counts).fetchall()

#2
no_tweets = select([func.count(dbtweets.c.id)]).select_from(dbtweets).where(dbtweets.c.user == dbusers.c.id).correlate(dbusers)
average_tags_per_tweet = select([dbusers.c.name, 
                                 (func.count(dbhashtags.c.hashtag)/no_tweets).label('average_tags_per_tweet')
                               ]).select_from(dbusers.join(dbtweets).join(dbhashtags)).group_by('tw_users.name')
results2 = conn.execute(average_tags_per_tweet).fetchall()

#3
day_tweets = select([func.dayname(dbtweets.c.created).label('weekday'),
                     dbusers.c.name.label('candidate'),
                     func.count(dbtweets.c.id).label('no_tweets')
                   ]).select_from(dbusers.join(dbtweets)).\
                   group_by('weekday').group_by('candidate').\
                   order_by('candidate').order_by(func.dayofweek(dbtweets.c.created))
results3 = conn.execute(day_tweets).fetchall()

#4
user_mentions = select([dbusers.c.name, func.count(dbmentions.c.tweet_id).label('times_mentioned')]).\
                select_from(dbusers.join(dbmentions)).\
                group_by('tw_users.name').order_by(desc('times_mentioned'))
results4 = conn.execute(user_mentions).fetchall()

# #5
# u = alias(dbusers, 'u')
# ca = alias(dbusers, 'ca')
# candidate_mentions_user = select([u.c.name.label('user_mentioned'), ca.c.name.label('candidate'),
#                                   func.count(dbmentions.c.tweet_id).label('no_mentions')
#                                 ]).select_from(u.join(dbmentions).join(dbtweets).join(ca)).\
#                                 where(ca.c.name.in_(("Hillary Clinton", "Donald J. Trump"))).\
#                                 group_by('u.name').group_by('ca.name').\
#                                 order_by('u.name').order_by('ca.name')
# results5 = conn.execute(candidate_mentions_user).fetchall()