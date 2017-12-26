#
# Script to import tweets from a CSV
# file or string and store them for
# later tweeting.
#
# The format of the CSV should be:
#
#   date,tweet_text,[optional url]
#
# Version: 1.0
#
from schtweet.storage import TweetStore

from datetime import datetime
from datetime import timedelta
from dateutil import parser
from collections import namedtuple
import pytz
import csv
import io
import argparse

ImportedRow = namedtuple('ImportedRow', 'date, tweet, url')

VERBOSE = False
def verbose_log(message):
    if VERBOSE:
        print(message)

def parse_row(row, default_timezone):
    """Parses a CSV row and returned the data in the named tuple ImportedRow."""
    row_date_string = row[0]
    row_date = parser.parse(row_date_string, dayfirst=True)
    if row_date.tzinfo is None:
        row_date = default_timezone.localize(row_date)
        verbose_log('No timezone info found, added timezone {}'.format(row_date.tzinfo))
    else:
        verbose_log('Detected timezone info: {}'.format(row_date.tzinfo))

    row_tweet = row[1]
    if len(row) > 2:
        row_url = row[2]

    return ImportedRow(row_date, row_tweet, row_url)

def parse_csv(csv_input, db_output, default_timezone):
    """Iterate over CSV lines, parsing each and appending it to the specified storage."""
    reader = csv.reader(csv_input)
    row_count = 0
    verbose_log('Writing to storage: {}'.format(db_output))
    with TweetStore(storage_name=db_output) as ts:
        for row in reader:
            row_count += 1
            verbose_log('Reading row {}'.format(row_count))
            record = parse_row(row, default_timezone)
            verbose_log('Scheduling tweet: date="{}", tweet="{}", url="{}"'.format(record.date, record.tweet, record.url))
            ts.schedule_tweet(record.date, record.tweet, record.url)
    print('Imported {} rows'.format(row_count))

def parse_csv_file(args):
    verbose_log('Reading CSV from file: {}'.format(args.csv_file))
    with io.open(args.csv_file, 'r', encoding='utf8') as csvfile:
        parse_csv(csvfile, args.output, pytz.timezone(args.timezone))

def parse_csv_string(args):
    verbose_log('Reading CSV from string: {}'.format(args.csv_string))
    parse_csv(args.csv_string.splitlines(), args.output, pytz.timezone(args.timezone))

########################################
# Set up the CLI parse
cli_main_parser = argparse.ArgumentParser()
cli_main_parser.add_argument('-v', '--verbose', help='Say all the things', action='store_true')
cli_main_parser.add_argument('-t', '--timezone', help='The timezone to apply to dates without timzeone information', default='Europe/London')
cli_main_parser.add_argument('-o', '--output', help='The name of the file to append the imported data to. Will be creataed if it does not exist.', default='scheduled-tweets.db')
cli_child_parsers = cli_main_parser.add_subparsers(dest='command', title='Commands')
cli_child_parsers.required = True

cli_csv_parser = cli_child_parsers.add_parser('csv', help="Import from CSV file")
cli_csv_parser.add_argument('csv_file', help='The CSV file to import tweets from. Should have the format: date,tweet_text,[optional url]')
cli_csv_parser.set_defaults(func=parse_csv_file)

cli_csv_parser = cli_child_parsers.add_parser('string', help="Import from CSV string")
cli_csv_parser.add_argument('csv_string', help='A CSV string to import a tweet from. Should have the format: date,tweet_text,[optional url]')
cli_csv_parser.set_defaults(func=parse_csv_string)

########################################
# Parse the command line and perform
# the user's bidding
args = cli_main_parser.parse_args()
if args.verbose:
    VERBOSE = True
args.func(args)
