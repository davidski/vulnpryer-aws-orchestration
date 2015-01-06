#!/usr/bin/python

# script for starting, monitoring and stopping the VulnPryer worker instance.
# Takes two parameters AWS region and OpsWorks ID of the VulnPryer instance

import time
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--opsworks_region', type=str, default="us-east-1",
                    help="OpsWorks region")
parser.add_argument('-i', '--instance_id', type=str,
			default="1feeb963-a339-44b0-ad57-bcb2e53bc111",
                    help="VulnPryer OpsWorks Instance ID")

parser.add_argument('-vn', '--vulnpryer_pipeline_metric_nspace', default='DataPipeline',
                    type=str,
                    help='Custom Cloudwatch metric namespace used for ' +
                         'ELK Pipeline')
parser.add_argument('-vm', '--vulnpryer_pipeline_metric_name', default='VulnpryerRunning',
                    type=str,
                    help='Custom Cloudwatch metric name used for ' +
                    'VulnPryer Pipeline')


args = parser.parse_args()
region = args.opsworks_region
opsworks_id = args.instance_id
vulnpryer_pipeline_metric_namespace = args.vulnpryer_pipeline_metric_nspace
vulnpryer_pipeline_metric_name = args.vulnpryer_pipeline_metric_name

# get status of the opsworks instance
import boto.opsworks

# Trigger population custom Cloudwatch metric for the pipeline
os.system("echo '* * * * * /usr/bin/aws cloudwatch put-metric-data " +
          "--metric-name " +
          vulnpryer_pipeline_metric_name + " --namespace " +
          vulnpryer_pipeline_metric_namespace +
          " --value 1 --region " + region + "' | crontab -")


print 'Start time: ' + time.ctime()
print 'Getting status of OpsWorks instance ' + opsworks_id + \
      ' on region ' + region
opsworks = boto.opsworks.connect_to_region(region)
print opsworks

instances = opsworks.describe_instances(instance_ids=[opsworks_id]).items()
for key, value in instances:
    status = value[0].get('Status')
failed_run = True
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

        if status == "online":
            failed_run = False

cw_cmd = "crontab -r && echo '* * * * * /usr/bin/aws cloudwatch put-metric-data " + \
         "--metric-name " + \
         vulnpryer_pipeline_metric_name + " --namespace " + \
         vulnpryer_pipeline_metric_namespace + \
         " --value 0 --region " + region + "' | crontab -"

if failed_run:
    os.system(cw_cmd)
    time.sleep(60)
    raise Exception("Failed run.. exiting..")

os.system(cw_cmd)
time.sleep(60)
exit(0)
