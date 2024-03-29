# copy_snapshots_no_x_account_
# This lambda function will copy source RDS snapshots that match the regex specified in the environment variable PATTERN into DEST_REGION. This function will need to run as many times necessary for the workflow to complete.
# Set PATTERN to a regex that matches your RDS isntance identifiers 
# Set DEST_REGION to the destination AWS region
import os
import sys
from os.path import dirname, abspath
sys.path.insert(0, "{}/lib".format(dirname(abspath(__file__))))

import boto3
from datetime import datetime
import time
import logging
import re
from snapshots_tool_utils.snapshots_tool_utils import *

# Initialize everything
LOGLEVEL = os.getenv('LOG_LEVEL', 'ERROR').strip()
PATTERN = os.getenv('SNAPSHOT_PATTERN', 'ALL_SNAPSHOTS')
DESTINATION_REGION = os.getenv('DEST_REGION').strip()
KMS_KEY_DEST_REGION = os.getenv('KMS_KEY_DEST_REGION', 'None').strip()
KMS_KEY_SOURCE_REGION = os.getenv('KMS_KEY_SOURCE_REGION', 'None').strip()
RETENTION_DAYS = int(os.getenv('RETENTION_DAYS'))
TIMESTAMP_FORMAT = '%Y-%m-%d-%H-%M'

if os.getenv('REGION_OVERRIDE', 'NO') != 'NO':
    REGION = os.getenv('REGION_OVERRIDE').strip()
else:
    REGION = os.getenv('AWS_DEFAULT_REGION')


logger = logging.getLogger()
logger.setLevel(LOGLEVEL.upper())



def handler(event, context):
    # Describe all snapshots
    pending_copies = 0
    client = boto3.client('rds', region_name=REGION)
    response = paginate_api_call(client, 'describe_db_snapshots', 'DBSnapshots')

    source_snapshots = get_own_snapshots_source(PATTERN, response)
    own_snapshots_encryption = get_own_snapshots_dest(PATTERN, response)

    # Get list of snapshots in DEST_REGION
    client_dest = boto3.client('rds', region_name=DESTINATION_REGION)
    response_dest = paginate_api_call(client_dest, 'describe_db_snapshots', 'DBSnapshots')
    dest_snapshots = get_own_snapshots_dest(PATTERN, response_dest)


    for source_identifier, source_attributes in source_snapshots.items():
        creation_date = get_timestamp(source_identifier, source_snapshots)
        if creation_date:
            time_difference = datetime.now() - creation_date
            days_difference = time_difference.total_seconds() / 3600 / 24

            # Only copy if it's newer than RETENTION_DAYS
            if days_difference < RETENTION_DAYS:
            # Copy to DESTINATION_REGION
                if source_identifier not in dest_snapshots.keys() and REGION != DESTINATION_REGION:
                    if source_snapshots[source_identifier]['Status'] == 'available':
                        try:
                            copy_remote(source_identifier, own_snapshots_encryption[source_identifier])
                 
                        except Exception:
                            pending_copies += 1
                            logger.error('Remote copy pending: %s: %s' % (
                                source_identifier, source_snapshots[source_identifier]['Arn']))
                    else:
                        pending_copies += 1
                        logger.error('Remote copy pending: %s: %s' % (
                            source_identifier, source_snapshots[source_identifier]['Arn']))
            else:
                logger.info('Not copying %s. Older than %s days' % (source_identifier, RETENTION_DAYS))

        else: 
            logger.info('Not copying %s. No valid timestamp' % source_identifier)
    else: 
	    logger.debug('No further snapshots found')
		
    if pending_copies > 0:
        log_message = 'Copies pending: %s. Needs retrying' % pending_copies
        logger.error(log_message)
        raise SnapshotToolException(log_message)


if __name__ == '__main__':
    handler(None, None)
