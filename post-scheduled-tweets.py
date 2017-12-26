#
# Script to tweet tweets which have been
# scheduled.
#
#
# Version: 1.0
#
from schtweet.storage import TweetStore
from collections import namedtuple
import io
import argparse
import twitter
import shutil
import os

AccessInformation = namedtuple('AccessInformation', 'consumer_key, consumer_secret, access_token_key, access_token_secret')

NO_POST = False
VERBOSE = False
def verbose_log(message):
    if VERBOSE:
        print(message)

def fetch_access_information(access_file):
    """Loads access information from a file."""
    line = ''
    with io.open(access_file, 'r', encoding='utf8') as file:
        line = file.readline()
        line = ' '.join(line.split())
    parts = line.split(' ')

    if not len(parts) == 4:
        raise SystemExit('Could to read all parts from {}. Expected line with: <consumer_key> <consumer_secret> <access_token_key> <access_token_secret>'.format(access_file))

    return AccessInformation(parts[0], parts[1], parts[2], parts[3])

def post_tweets_from_file(storage_file, access):
    verbose_log('Connecting with consumer_key="{}", access_token_key="{}"'.format(access.consumer_key, access.access_token_key))
    twitter_api = twitter.Api(**access._asdict())

    processed_tweets = 0
    sent_tweets = 0

    def process_scheduled_tweet(tweet_text, scheduled_date):
        verbose_log("Got tweet: '{}', due to be sent on {}".format(tweet_text, scheduled_date))
        nonlocal processed_tweets
        processed_tweets += 1
        tweet_id = None
        try:
            status = None
            if NO_POST:
                print('Would have posted "{}"', tweet_text)
            else:
                status = twitter_api.PostUpdate(tweet_text)
                tweet_id = status.id_str
            if status is not None:
                nonlocal sent_tweets
                sent_tweets += 1
                succeeded = True
        except Exception as e:
            print('Failed to send tweet "{}". Exception: {}', tweet_text, e)

        return tweet_id

    with TweetStore(storage_file) as ts:
        ts.process_due_tweets(process_scheduled_tweet)

    print('Number of tweets processed: {}'.format(processed_tweets))
    print('     Number of tweets sent: {}'.format(sent_tweets))

########################################
# Set up the CLI parse
cli_main_parser = argparse.ArgumentParser()
cli_main_parser.add_argument('-v', '--verbose', help='Say all the things', action='store_true')
cli_main_parser.add_argument('-n', '--nopost', help='Do everything except send tweets', action='store_true')
cli_main_parser.add_argument('-s', '--showcron', help='Show an entry suitable for calling this script every 5 minutes via crontab. After showing the crontab entry, exit without posting tweets.', action='store_true')
cli_main_parser.add_argument('-c', '--credentials', help='File containing the credentials to tweet with. Should be a single line of the format (values are just space separated): consumer_key consumer_secret access_token_key access_token_secret', default='access')
cli_main_parser.add_argument('storage_file', help='The name of the file to read the scheduled tweets from. Will be updated after the tweet is sent.')

########################################
# Parse the command line and perform
# the user's bidding
args = cli_main_parser.parse_args()

if args.verbose:
    VERBOSE = True
if args.nopost:
    NO_POST = True

if args.showcron:
    pipenv_location = shutil.which('pipenv')
    script_location = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
    script_name = os.path.basename(__file__)
    storage_location = os.path.abspath(os.path.realpath(args.storage_file))
    credentials_location = os.path.abspath(os.path.realpath(args.credentials))

    command = "cd '{}' && '{}' run python post-scheduled-tweets.py --credentials '{}' '{}'".format(
        script_location, pipenv_location, credentials_location, storage_location)

    cron = "*/5 * * * * {}".format(command)

    print(cron)
else:
    verbose_log('Reading access information from "{}"'.format(args.credentials))
    access = fetch_access_information(args.credentials)

    print('Started processing scheduled tweets from "{}"'.format(args.storage_file))
    post_tweets_from_file(args.storage_file, access)
    print('Finished processing scheduled tweets from "{}"'.format(args.storage_file))
