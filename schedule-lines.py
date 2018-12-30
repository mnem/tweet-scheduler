#
# Script to process lines in a text file
# and output them to a CSV file suitable
# for importing with import-tweets.py.
#
# Each line is assumed to contain a single tweet.
# This is then scheduled according to the values
# passed to the script.
#
# The output format is:
#
#   date,tweet_text
#
# Version: 1.0
#
import argparse
import datetime
import os
from typing import TextIO

COMMENT_PREFIX = '//'

VERBOSE = False


def verbose_log(message):
    """Logs a message to stdout if verbose"""
    if VERBOSE:
        print(message)


def parse_start_date(start_date_str):
    try:
        components = [int(x.strip()) for x in start_date_str.split('/')]
        if len(components) > 3:
            raise Exception('Too many date components')
    except Exception as e:
        raise SystemExit('{}\nUnexpected start date. '
                         'Expected format dd/mm/yyyy, found: "{}".'.format(e, start_date_str))

    now = datetime.datetime.now()
    if len(components) == 0:
        components.append(now.day)

    if len(components) == 1:
        components.append(now.month)

    if len(components) == 2:
        components.append(now.year)

    return datetime.datetime(components[2], components[1], components[0])


def parse_times(times_str):
    try:
        entries = [datetime.datetime.strptime(x.strip(), '%H%M') for x in times_str.split(',') if len(x.strip()) > 2]
        if len(entries) == 0:
            raise Exception('No times found')
    except Exception as e:
        raise SystemExit('{}\nUnexpected times format. Expected "1830[,1930,0200]", found "{}".'.format(e, times_str))

    return entries


def escape_line_for_csv(line):
    if ',' in line or '"' in line:
        return '"' + line.replace('"', '""') + '"'
    else:
        return line


def process_lines(input_filename, output_filename, first_day, times, overwrite):
    verbose_log('     Input: {}'.format(input_filename))
    verbose_log('    Output: {}'.format(output_filename))
    verbose_log('Overwritet: {}'.format(overwrite))
    verbose_log(' First day: {}'.format(first_day.isoformat()))
    verbose_log('     Times: {}'.format([x.strftime('%H%M') for x in times]))
    verbose_log('     Input: {}\n'.format(input_filename))

    print('Processing tweets from {} and {} output file {}'.format(
        input_filename,
        'overwriting' if overwrite else 'appending to',
        output_filename))

    current_time_index = 0
    current_day = first_day
    num_lines = 0
    num_scheduled = 0
    with open(input_filename, 'r') as input_file:
        if overwrite:
            mode = 'w'
        else:
            mode = 'a'

        with open(output_filename, mode) as output_file:  # type: TextIO
            for line in input_file:
                line = line.strip()
                if line.startswith(COMMENT_PREFIX):
                    verbose_log('Skipping comment: {}'.format(line))
                    continue

                num_lines += 1
                if len(line) > 0:
                    schedule = datetime.datetime(current_day.year, current_day.month, current_day.day,
                                                 hour=times[current_time_index].hour,
                                                 minute=times[current_time_index].minute)
                    output_line = '{},{}'.format(schedule.strftime('%d/%m/%Y %H:%M'), escape_line_for_csv(line))
                    output_file.write('{}\n'.format(output_line))
                    verbose_log('Entry: {}'.format(output_line))

                    num_scheduled += 1
                else:
                    verbose_log('Skipping next time slot because of empty line')

                current_time_index += 1
                if current_time_index >= len(times):
                    current_time_index = 0
                    current_day += datetime.timedelta(days=1)

        print('Scheduled {} tweets into {} time slots.'.format(num_scheduled, num_lines))


########################################
# Set up the CLI parse
cli_main_parser = argparse.ArgumentParser()
cli_main_parser.add_argument('-v', '--verbose',
                             help='Say all the things',
                             action='store_true')
cli_main_parser.add_argument('-s', '--start',
                             help='The initial date to schedule the lines from. Specified '
                                  'as dd/mm/yyyy. You can omit year, year and month or year, '
                                  'month and day. Omitted fields default to the current date.',
                             default=datetime.datetime.now().strftime('%d/%m/%Y'))
cli_main_parser.add_argument('-o', '--output',
                             help='The name of the file to append the imported data to.'
                                  ' Will be created if it does not exist.',
                             default='scheduled-lines.csv')
cli_main_parser.add_argument('-x', '--overwrite',
                             help='Overwrite the output file. The default is to append.',
                             action='store_true')
cli_main_parser.add_argument('-t', '--times',
                             help='The times to schedule the tweets within the day. Comma '
                                  'separated 24h format strings. Lines will be scheduled in order '
                                  'of these times, so if you specify 3 times, 3 tweets will be '
                                  'scheduled for each day from the input lines. 1 time will cause '
                                  '1 tweet to be sent per day. For example, to send one tweet in '
                                  'the morning and one in the evening, you could specify: 0900,2100.',
                             default='1200')
cli_main_parser.add_argument('lines_file',
                             help='The name of the file to read the tweet lines to be scheduled from.')

########################################
# Parse the command line and perform
# the user's bidding
args = cli_main_parser.parse_args()
if args.verbose:
    VERBOSE = True

process_lines(
    os.path.abspath(args.lines_file),
    os.path.abspath(args.output),
    parse_start_date(args.start),
    parse_times(args.times),
    args.overwrite)
