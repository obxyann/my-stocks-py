# little assistant not ass

from datetime import datetime, timedelta
import re
import platform
import os

# return YYYMMDD or YYYY[separator]MM[separator]DD
def get_last_market_close_day (close_hour = 15, close_minute = 0, min_guo_year = False, separator = None):
    # current time
    curr_time = datetime.now()

    weekday = curr_time.weekday()   # 0~6

    # market closing time of today
    market_close = curr_time.replace(hour = close_hour, minute = close_minute, second = 0, microsecond = 0)

    # check to adjust the market closing time
    if weekday < 5 and curr_time > market_close:
        # this is a workday and after market closed today
        # use today's market_close
        days_ago = 0
    else:
        if weekday == 0:
            # this is Monday and before today's market closing
            days_ago = 3
        elif weekday < 5:
            # this is a workday (not Monday) and before today's market closing
            days_ago = 1
        else:
            # this is the weekend
            days_ago = weekday - 4

        # use the last market closed time
        market_close = market_close - timedelta(days = days_ago)

    if min_guo_year:
        year = market_close.year - 1911
    else:
        year = market_close.year

    if not separator:
        return f'{year}{market_close.month:02}{market_close.day:02}'

    return f'{year}{separator}{market_close.month:02}{separator}{market_close.day:02}'

# Get date part '20241108' from path\any_text_20241108.ext
#                            or path\any_text_1131108.ext
#
# return date string in YYYYMMDD
#        or empty string if failed
def get_date_from_path_name (path_name):
    # case 1: path\STOCK_DAY_ALL_20241108.csv
    # case 2: path\RSTA3104_1131108.csv
    match = re.search(r'_([0-9]{7,8}).csv', path_name)

    if match:
        date = match.group(1)

        if len(date) == 8:
            # case 1: -> 20241108
            return date

        # case 2: 1131108 -> 20241108
        return str(int(date[:3]) + 1911) + date[3:]
    else:
        raise Exception(f'Can\'t get date string from \'{path_name}\'')

    return ''

#############
# file time #
#############

def creation_time (path_name):
    '''
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation
    '''
    if platform.system() == 'Windows':
        return os.path.getctime(path_name)
        '''
        Note: A file's ctime on Windows is slightly different than on Linux
              Windows users know theirs as 'creation time'
              Linux users know theirs as 'change time' (by writing or by setting owner, group, link count, mode, etc.)
        '''
    else:
        stat = os.stat(path_name)
        try:
            return stat.st_birthtime

        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified
            return stat.st_mtime

def modification_time (path_name):
    return os.path.getmtime(path_name)

def file_is_old (path_name, hour = 0, minute = 0, second = 0, quiet = True):
    if not os.path.isfile(path_name):
        quiet or print(f'Checking \'{path_name}\' ...')
        quiet or print(f'    {EXCLAMATION_MARK} Missed')
        return True

    if not os.path.getsize(path_name):
        quiet or print(f'Checking \'{path_name}\' ...')
        quiet or print(f'    {EXCLAMATION_MARK} Size is zero')
        return True

    file_time = datetime.fromtimestamp(modification_time(path_name))
    # or for debug
    # file_time = datetime(2024, 11, 3, 17, 31, 00)
    curr_time = datetime.now()
    last_time = curr_time.replace(hour = hour, minute = minute, second = second, microsecond = 0)

    quiet or print(f'Checking \'{path_name}\' @ {file_time} ...')
    quiet or print(f'    Now is {curr_time}')
    quiet or print(f'    Recent update is at {last_time}')

    if (curr_time > last_time):
        quiet or print(f'    Update data is availabe')

        if (file_time > last_time):
            quiet or print('    File is updated')
            return False

        quiet or print('    File need to update')
        return True

    quiet or print('    Not yet to today\'s update time')

    last_time -= timedelta(days = 1)

    quiet or print(f'    Yesterday update is available at {last_time}')

    if (file_time > last_time):
        quiet or print('    File is updated yesterday (not yet to today\'s update time)')
        return False

    quiet or print('    File need to update to yesterday\'s update')
    return True

#############
# directory #
#############

# Create directory if it doesn't exist
def ensure_directory_exists (path_name):       
    dir_name = os.path.dirname(path_name)
    
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok = True)

##########
# backup #
##########

# import os
import time
import zipfile

D_ARROW = '\u2193'      # '↓' U+2193
R_ARROW = '\u2192'      # '→' U+2192
BALLOT_X = '\u2717'     # '✗' U+2718
# BALLOT_X = '\u2718'   # '✘' U+2718 (Heavy Ballot X)
EXCLAMATION_MARK = '!'  # U+0021
CHECK_MARK = '\u2713'   # '✓' U+2713
# CHECK_MARK = '\u2714' # '✔' U+2714 (Heavy Check Mark)

# param
#   path_name   file path to backup
#               NOTE: it will rename to 'path\base_name_YYYMMDD_HHMM.ext' first
#   zip_path    None for just renaming no zipping or add to this zip file
#
# return True for completion or False
def backup_file (path_name, zip_path = None):
    if os.path.isfile(path_name):
        ts = int(modification_time(path_name))

        print(f'Zipping \'{path_name}\' @ {datetime.fromtimestamp(ts)} ...')

        year, month, mday, hour, minute, sec = time.localtime(ts)[:-3]

        base = os.path.basename(path_name)
        name, ext = os.path.splitext(base)

        # dst_path = f'{name}_{year}{month:02}{mday:02}_{hour:02}{minute:02}{sec:02}{ext}'
        # or
        dst_path = f'{name}_{year}{month:02}{mday:02}_{hour:02}{minute:02}{ext}'

        if zip_path != None:
            print(f'    {R_ARROW} {dst_path}')  # DOWNWARDS ARROW, U+2193
            print(f'    {R_ARROW} {zip_path}')  # RIGHTWARDS ARROW, U+2192

            try:
                with zipfile.ZipFile(zip_path, 'a', compression = zipfile.ZIP_DEFLATED) as zipf:
                    if dst_path in zipf.namelist():
                        print(f'    {EXCLAMATION_MARK} Duplicate name \'{dst_path}\'') # HEAVY BALLOT X, U+2718
                        return 'skipped'
                    else:
                        zipf.write(path_name, dst_path)

            except zipfile.BadZipFile:
                print(f'    {BALLOT_X} Bad or not a zip file')
                return 'failed'
            except Exception as error:
                print(f'    {BALLOT_X} {error}')
                return 'failed'
        else:
            print(f'    {R_ARROW} {dst_path}')
            try:
                os.rename(path_name, dst_path)

            except FileExistsError:
                print(f'    {BALLOT_X} Destination file already exists')
                return 'skipped'
            except PermissionError:
                print(f'    {BALLOT_X} You don\'t have permissions to rename the file')
                return 'failed'
            except OSError as error:
                print(f'    {BALLOT_X} {error}')
                return 'failed'
    else:
        print(f'Zipping \'{path_name}\' ...')
        print(f'    {EXCLAMATION_MARK} File not found!')
        return 'skipped'

    print('    Done')

    return 'done'

# param
#   files       file list to backup, E.g. ['file1.txt', 'file2']
#               NOTE: it will rename to 'path\base_name_YYYMMDD_HHMM.ext' first
#   zip_path    None for just renaming no zipping or add to this zip file
#
# return True for completion or False
def backup_files (files, zip_path = None):
    results = []

    # files = [
    #     f'{data_dir}/open.csv',
    #     f'{data_dir}/close.csv',
    #     f'{data_dir}/high.csv',
    #     f'{data_dir}/low.csv',
    #     f'{data_dir}/volume.csv',
    #     f'{data_dir}/revenue.csv']

    for file in files:
        result = backup_file(file, zip_path)

        if result == 'failed' and not to_continue():
            return False

        results.append(result)

    skipped = failed = added = 0

    for result in results:
        if result == 'skipped':
            skipped += 1
        elif result == 'failed':
            failed += 1
        else: # if result == 'done':
            added += 1

    if failed:
        print(f'Backup incompleted ({skipped} skipped {failed} failed {added} added)')
        return False
    elif skipped:
        print(f'Backup warning ({skipped} skipped {added} added)')
        return False

    return True

#######
# ask #
#######

def to_continue (question = 'Do you want to continue?'):
    while True:
        user_input = input(f'{question} (yes/no): ')

        answer = user_input.lower()

        if answer in ['yes', 'y']:
            return True
        if answer in ['no', 'n']:
            return False
        # if not answer:
        #    return False

        # ask again

###########
# spinner #
###########

# ref:
# https://stackoverflow.com/questions/48854567/how-do-i-make-an-asynchronous-progress-spinner-in-python

import sys
# import time
import threading
import random

spin_done = None
spin_thread = None

def spin_cursor ():
    while True:
        for cursor in '|/-\\':
            sys.stdout.write(cursor)
            sys.stdout.flush()
            time.sleep(0.1)         # adjust this to change the speed
            sys.stdout.write('\b')
            # if spin_done.is_set():
            if spin_done:
                return

# start the spinner in a separate thread
def spinner_start ():
    global spin_done, spin_thread

    # spin_done = threading.Event()
    spin_done = False

    spin_thread = threading.Thread(target = spin_cursor)
    spin_thread.start()

# tell the spinner to stop, and wait for it to do so
# this will clear the last cursor before the program moves on
def spinner_end ():
    global spin_done

    # spin_done.set()
    spin_done = True

    spin_thread.join()

# wait N sceonds, for 0 < a <= N <= b
def wait (a, b):
    secs = random.uniform(a, b) 

    if secs > 0:
        spinner_start()
        time.sleep(secs)
        spinner_end()
