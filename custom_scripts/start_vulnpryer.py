#!/usr/bin/python

# Script for starting, monitoring and stopping the Vulnpryer worker instance.
# Takes two parameters AWS region and Opswork ID of the Vulnpryer Instance

import time 
region = '<aws_region>'
opswork_id = '<instance_id>'


# Get Status of the Opswork instance
import boto.opsworks
print 'Start time: ' + time.ctime()
print 'Getting status of Opswork instance ' + opswork_id + ' on region ' + region
opswork = boto.opsworks.connect_to_region(region)
for key, value in opswork.describe_instances(instance_ids=[opswork_id]).items() :
  status = value[0].get('Status')

if status == 'stopped' :
  
  # Start Vulnpryer
  print 'Starting Vulnpryer worker'
  opswork.start_instance(opswork_id)
 
  # Wait for result. Continually check status 
  while True : 
    for key, value in opswork.describe_instances(instance_ids=[opswork_id]).items() :
      status = value[0].get('Status')

    print time.ctime() + ':Instance in ' + status + ' status.'
    if status in ['online', 'stopped', 'start_failed', 'setup_failed', 'terminating', 'shutting_down', 'terminated'] :
      break

    time.sleep(60)

  # Stop Vulnpryer
  if status in ['online', 'start_failed', 'setup_failed'] :
    print 'Stopping Vulnpryer worker'
    opswork.stop_instance(opswork_id)

    if status in ['start_failed', 'setup_failed'] :
      raise Exception('Failure was encountered while trying to setup and run Vulnpryer. Please check logs of the Opsworks instance')
    else :
      print 'Vulnpryer completed successfully'
 
  else :
    raise Exception('Vulnpryer instance is in ' + status + ' state which was unexpected. Another process or a user could have requested shut down of the instance.')

else :
  raise Exception('Vulnpryer instance expected status is stopped. It is currently ' + status + '. Another process could be already be running.')
  

