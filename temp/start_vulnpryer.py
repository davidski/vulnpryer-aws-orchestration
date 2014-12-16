#!/usr/bin/python
 
# script for starting, monitoring and stopping the VulnPryer worker instance.
# Takes two parameters AWS region and OpsWorks ID of the VulnPryer instance
 
# import sys
import time
import argparse
 
parser = argparse.ArgumentParser()
parser.add_argument('-r', '--region', type=str, default="us-east-1",
                    help="OpsWorks region")
parser.add_argument('-i', '--instance-id', type=str,
			default="0d4c366a-0ea7-4f5d-9e02-37549aec38af",
                    help="VulnPryer OpsWorks Instance ID")
args = parser.parse_args()
region = args.region
opsworks_id = args.instance_id
 
# get status of the opsworks instance
import boto.opsworks
print 'Start time: ' + time.ctime()
print 'Getting status of OpsWorks instance ' + opsworks_id + \
      ' on region ' + region
opsworks = boto.opsworks.connect_to_region(region)
print opsworks
 
instances = opsworks.describe_instances(instance_ids=[opsworks_id]).items()
for key, value in instances:
    status = value[0].get('Status')
 
if status == 'stopped':
 
    # start vulnpryer
    print 'Starting VulnPryer worker'
    opsworks.start_instance(opsworks_id)
 
    # wait for result. continually check status
    while True:
        instances = opsworks.describe_instances(instance_ids=[opsworks_id]) \
                            .items()
        for key, value in instances:
            status = value[0].get('Status')
 
        print time.ctime() + ':Instance in ' + status + ' status.'
        if status in ['online', 'stopped', 'start_failed', 'setup_failed',
                      'terminating', 'shutting_down', 'terminated']:
            break
 
        time.sleep(60)
 
    # stop VulnPryer
    if status in ['online', 'start_failed', 'setup_failed']:
        print 'Stopping VulnPryer worker'
        opsworks.stop_instance(opsworks_id)
 
        if status in ['start_failed', 'setup_failed']:
            raise Exception('Failure was encountered while trying to setup \
                            and run VulnPryer. Please check logs of the \
                            OpsWorks instance')
        else:
            print 'VulnPryer completed successfully'
    else:
        raise Exception('VulnPryer instance is in ' + status +
                        ' state which was unexpected. Another process or a \
                        user could have requested shut down of the instance.')
else:
    raise Exception('VulnPryer instance expected status is stopped. It \
                    is currently ' + status + '. Another process could be \
                    already running.')
