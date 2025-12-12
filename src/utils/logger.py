import logging
import os
from datetime import datetime

# globals
file_logger = None  # calling the logger's debug(), info(), warning(), error()

start_time = None


# NOTE: this log will not add a newline after message
def log(msg, quiet=False):
    if not quiet:
        print(msg, end='', flush=True)
    if file_logger:
        file_logger.info(msg)


def logger_start(
    log_name='log', log_ext='.txt', log_dir='.', add_start_time_to_name=True
):
    # create a file logger
    global file_logger, start_time

    start_time = datetime.now()

    os.makedirs(log_dir, exist_ok=True)

    if add_start_time_to_name:
        path_name = f'{log_dir}/{log_name}_{start_time.strftime("%Y%m%d_%H%M")}{log_ext}'  # fmt: skip
    else:
        path_name = f'{log_dir}/{log_name}{log_ext}'

    file_logger = setup_file_logger(path_name, end='')

    if not add_start_time_to_name:
        # add a start time line at begin
        file_logger.info(f'=== {start_time.strftime("%Y/%m/%d %H:%M:%S")} Begin ===\n')


def logger_end():
    # NOTE: It's risky to measure elapsed time by two datetime.now() because
    #       datetime.now() may be changed by like network time syncing, daylight savings switchover
    #       or the user twiddling the clock
    end_time = datetime.now()

    if start_time:
        time_elapsed = end_time - start_time

        # add a line at end
        # file_logger.info(f'=== {end_time.strftime("%Y/%m/%d %H:%M:%S")} End ({time_elapsed} elapsed) ===\n\n')
        # or
        file_logger.info(f'({time_elapsed} elapsed)\n\n')

        return time_elapsed

    # add a line at end
    # file_logger.info(f'=== {end_time.strftime("%Y/%m/%d %H:%M:%S")} End ===\n\n')
    # or
    file_logger.info(f'({end_time.strftime("%Y/%m/%d %H:%M:%S")})\n\n')

    return None


# return Logger
def setup_file_logger(path_name='log.txt', end='\n'):
    try:
        # get the logger
        #
        # NOTE: multiple calls to getLogger() with the same name will return a reference
        #       to the same logger object
        logger = logging.getLogger(__name__)

        logger.setLevel(logging.INFO)

        # create a file handler
        fh = logging.FileHandler(path_name)

        fh.setLevel(logging.INFO)

        # replace the default newline termination '\n'
        # see:
        # https://signoz.io/guides/how-to-insert-newline-in-python-logging
        # https://stackoverflow.com/questions/7168790/suppress-newline-in-python-logging-module
        # https://stackoverflow.com/questions/39507711/python-logging-terminator-as-option
        fh.terminator = end

        if hasattr(logger, '_last_added_fh'):
            # remove last added handler
            logger.removeHandler(logger._last_added_fh)

            logger._last_added_fh = None

        logger.addHandler(fh)

        logger._last_added_fh = fh

    except Exception as error:
        print(f'Error: {error}')

    return logger


def test():
    try:
        logger_start('log1')

        log('This is log1\n')

        # change logging to new file
        logger_start('log2')

        log('This is log2\n')

        logger_start('log1')

        log('Continue to log1\n')

    except Exception as error:
        print(f'Program terminated: {error}')
        return

    time_elapsed = logger_end()

    print(f'({time_elapsed} elapsed)')

    print('Goodbye!')


if __name__ == '__main__':
    test()
