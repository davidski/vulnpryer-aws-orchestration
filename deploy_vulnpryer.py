#!/usr/bin/python

import boto.datapipeline
import boto.ec2.cloudwatch
import boto.iam
import boto.opsworks
import boto.s3
import ConfigParser
import ast
import re
config = ConfigParser.ConfigParser()
config.read('deploy_vulnpryer.cfg')


def update_iam_role(iam, role_name, assume_role_policy_file,
                    permission_policy_file):

    try:
        iam.get_role(role_name)
    except:
        print role_name + ' role not found. Creating role '
        iam.create_role(role_name)

    print 'Updating assume role policy of ' + role_name
    with open(assume_role_policy_file, "r") as myfile:
        policy = myfile.read()
        iam.update_assume_role_policy(role_name, policy)

    print 'Updating attached permission policies of ' + role_name
    for rp in iam.list_role_policies(role_name).get('list_role_policies_response').get('list_role_policies_result').get('policy_names'):
        iam.delete_role_policy(role_name, rp)
    with open(permission_policy_file, "r") as myfile:
        policy = myfile.read()
        iam.put_role_policy(role_name, role_name + '_permission_policy', policy)

    try:
        iam.get_instance_profile(role_name)
    except:
        print role_name + ' instance profile not found. Creating instance profile'
        iam.create_instance_profile(role_name)
    print 'Updating role and instance profile association of ' + role_name
    for ip in iam.list_instance_profiles_for_role(role_name).get('list_instance_profiles_for_role_response').get('list_instance_profiles_for_role_result').get('instance_profiles'):
        iam.remove_role_from_instance_profile(role_name, role_name)
    iam.add_role_to_instance_profile(role_name, role_name)


# Prepare needed IAM roles
def define_iam_roles():
    print '------------------------------'
    print 'Preparing Vulnpryer IAM Roles'
    print '------------------------------'

    # Connect to AWS IAM
    try:
        iam = boto.iam.connect_to_region(region_name=config.get('general', 'iam_aws_region'), aws_access_key_id=config.get('general', 'aws_access_key_id'), aws_secret_access_key=config.get('general', 'aws_secret_access_key'))
        iam.get_account_alias()
    except:
        print "Check keys and configuration before proceeding."
        return False
    # Prepare Data Pipeline Roles
    update_iam_role(iam, config.get('data_pipeline', 'pipeline_role'), 'iam_policies/datapipeline_vulnpryer_role_trust', 'iam_policies/datapipeline_vulnpryer_role_policy')
    update_iam_role(iam, config.get('data_pipeline', 'pipeline_resource_role'), 'iam_policies/datapipeline_vulnpryer_resource_role_trust', 'iam_policies/datapipeline_vulnpryer_resource_role_policy')

    # Prepare Opsworks Roles
    # update_iam_role(iam, config.get('opsworks', 'opsworks_role'), 'iam_policies/opsworks_vulnpryer_role_trust', 'iam_policies/opsworks_vulnpryer_role_policy')
    update_iam_role(iam, config.get('opsworks', 'opsworks_resource_role'), 'iam_policies/opsworks_vulnpryer_resource_role_trust', 'iam_policies/opsworks_vulnpryer_resource_role_policy')

    print 'Successfully prepared IAM roles'
    return True


# Builds the Opsworks Stack
def build_opsworks_stack():
    print '------------------------------------'
    print 'Building Vulnpryer Opsworks Stack'
    print '------------------------------------'

    # Connect to AWS Opsworks
    ow = boto.opsworks.connect_to_region(region_name=config.get('general', 'opsworks_aws_region'), aws_access_key_id=config.get('general', 'aws_access_key_id'), aws_secret_access_key=config.get('general', 'aws_secret_access_key'))

    # Check if stack exists
    for stack in ow.describe_stacks().get('Stacks'):
        if stack.get('Name') == config.get('opsworks', 'stack_name'):
            print 'Stack ' + config.get('opsworks', 'stack_name') + ' exists. Deleting stack with Stack ID ' + stack.get('StackId')

            # Delete instances
            for instance in ow.describe_instances(stack_id=stack.get('StackId')).get('Instances'):
                ow.delete_instance(instance_id=instance.get('InstanceId'))

            ow.delete_stack(stack.get('StackId'))

    # Retrieve IAM ARNs
    iam = boto.iam.connect_to_region(region_name=config.get('general', 'opsworks_aws_region'), aws_access_key_id=config.get('general', 'aws_access_key_id'), aws_secret_access_key=config.get('general', 'aws_secret_access_key'))
    service_arn = iam.get_role(config.get('opsworks', 'opsworks_role')).get('get_role_response').get('get_role_result').get('role').get('arn')
    ip_arn = iam.get_instance_profile(config.get('opsworks', 'opsworks_resource_role')).get('get_instance_profile_response').get('get_instance_profile_result').get('instance_profile').get('arn')

    # Creating new Opworks Stack
    try:
        new_stack = ow.create_stack(config.get('opsworks', 'stack_name'), config.get('general', 'vpc_aws_region'), service_arn, ip_arn, vpc_id=config.get('opsworks', 'vpc_id'), default_os=config.get('opsworks', 'default_os'), default_subnet_id=config.get('opsworks', 'default_subnet_id'), custom_json=config.get('opsworks', 'custom_json'), configuration_manager=ast.literal_eval(config.get('opsworks', 'configuration_manager')), chef_configuration=ast.literal_eval(config.get('opsworks', 'chef_configuration')), use_custom_cookbooks=config.getboolean('opsworks', 'use_custom_cookbooks'), use_opsworks_security_groups=config.getboolean('opsworks', 'use_opsworks_security_groups'), custom_cookbooks_source=ast.literal_eval(config.get('opsworks', 'custom_cookbooks_source')), default_ssh_key_name=config.get('opsworks', 'default_ssh_key_name'))

        new_layer = ow.create_layer(new_stack.get('StackId'), 'custom', config.get('opsworks', 'layer_name'), config.get('opsworks', 'layer_short_name'), attributes=None, custom_instance_profile_arn=ip_arn, custom_security_group_ids=[config.get('opsworks', 'layer_security_group')], packages=None, volume_configurations=None, enable_auto_healing=True, auto_assign_elastic_ips=False, auto_assign_public_ips=True, custom_recipes=ast.literal_eval(config.get('opsworks', 'layer_custom_recipes')), install_updates_on_boot=True, use_ebs_optimized_instances=False)
    except:
        print "New stack failed to create. Check keys and configuration before proceeding."
        return False
    new_instance = ow.create_instance(new_stack.get('StackId'), [new_layer.get('LayerId')], config.get('opsworks', 'instance_type'), hostname=config.get('opsworks', 'instance_name'))
    print 'Successfully built Opsworks Stack ' + config.get('opsworks', 'stack_name') + ' with stack id ' + new_stack.get('StackId')
    return new_instance.get('InstanceId')


# Prepares the custom script
def prepare_custom_script(instance_id):
    print '------------------------------------'
    print 'Preparing Vulnpryer Custom Script'
    print '------------------------------------'

    f1 = open('custom_scripts/start_vulnpryer.py', 'r')
    f2 = open('temp/start_vulnpryer.py', 'w')
    for line in f1:
        line = re.sub(r"^.*--opsworks_region.*$", "parser.add_argument('-r', '--opsworks_region', type=str, default=\"" + config.get('general', 'opsworks_aws_region') + "\",", line)
        line = re.sub(r"^.*--instance_id.*$", "parser.add_argument('-i', '--instance_id', type=str,\n\t\t\tdefault=\"" + instance_id + "\",", line)
        line = re.sub(r"^.*--vulnpryer_pipeline_metric_nspace.*$", "parser.add_argument('-vn', '--vulnpryer_pipeline_metric_nspace', default=\'" + config.get('cloudwatch', 'vulnpryer_pipeline_metric_namespace') + "\',", line)
        line = re.sub(r"^.*--vulnpryer_pipeline_metric_name.*$", "parser.add_argument('-vm', '--vulnpryer_pipeline_metric_name', default=\'" + config.get('cloudwatch', 'vulnpryer_pipeline_metric_name') + "\',", line)
        f2.write(line)

    f1.close()
    f2.close()
    print 'Plugged in region ' + config.get('general', 'opsworks_aws_region') + ' and opsworks instance id ' + instance_id

    # Connect AWS S3
    try:
        s3 = boto.s3.connect_to_region(region_name=config.get('general', 's3_aws_region'), aws_access_key_id=config.get('general', 'aws_access_key_id'), aws_secret_access_key=config.get('general', 'aws_secret_access_key'))
        bucket = s3.get_bucket(config.get('custom_script', 's3_bucket'))
    except:
        print "Check keys and configuration before proceeding."
        return False

    k = bucket.get_key(config.get('custom_script', 's3_bucket_directory') + 'start_vulnpryer.py')
    if k is None:
        k = bucket.new_key(config.get('custom_script', 's3_bucket_directory') + 'start_vulnpryer.py')
    k.set_contents_from_filename('temp/start_vulnpryer.py')

    print 'Uploaded script ' + str(k)


# Prepares Pipeline Object Definition
def prepare_pipeline_object(definition):
    new_definition = definition.replace('<pipeline_role>', config.get('data_pipeline', 'pipeline_role'))
    new_definition = new_definition.replace('<pipeline_resource_role>', config.get('data_pipeline', 'pipeline_resource_role'))
    new_definition = new_definition.replace('<pipeline_aws_region>', config.get('general', 'pipeline_aws_region'))
    new_definition = new_definition.replace('<cw_aws_region>', config.get('general', 'cw_aws_region'))
    new_definition = new_definition.replace('<opsworks_aws_region>', config.get('general', 'opsworks_aws_region'))
    new_definition = new_definition.replace('<topic_arn>', config.get('data_pipeline', 'topic_arn'))
    new_definition = new_definition.replace('<script_path>', config.get('custom_script', 's3_bucket') + "/" + config.get('custom_script', 's3_bucket_directory'))
    new_definition = new_definition.replace('<vulnpryer_pipeline_metric_namespace>', config.get('cloudwatch', 'vulnpryer_pipeline_metric_namespace'))
    new_definition = new_definition.replace('<vulnpryer_pipeline_metric_name>', config.get('cloudwatch', 'vulnpryer_pipeline_metric_name'))
    return new_definition


def create_cloudwatch_alarm():
    print '---------------------------------------------------------'
    print 'Create CloudWatch Alarm for VulnPryer Pipeline'
    print '---------------------------------------------------------'

    cw = boto.ec2.cloudwatch.connect_to_region(region_name=config.get('general', 'cw_aws_region'),
                                               aws_access_key_id=config.get('general', 'aws_access_key_id'),
                                               aws_secret_access_key=config.get('general', 'aws_secret_access_key'))

    # Intialize Custom Cloudwatch metric
    cw.put_metric_data(namespace=config.get('cloudwatch', 'vulnpryer_pipeline_metric_namespace'),
                       name=config.get('cloudwatch', 'vulnpryer_pipeline_metric_name'), value=0)

    # (Re)create alarm
    cw.delete_alarms([config.get('cloudwatch', 'cw_alarm_vulnpryer_pipeline')])
    vulnpryer_pipeline_metric = cw.list_metrics(metric_name=config.get('cloudwatch', 'vulnpryer_pipeline_metric_name'),
                                                namespace=config.get('cloudwatch', 'vulnpryer_pipeline_metric_namespace'))
    print vulnpryer_pipeline_metric
    vulnpryer_pipeline_metric[0].create_alarm(config.get('cloudwatch', 'cw_alarm_vulnpryer_pipeline'), comparison='>', threshold=0, period=60, statistic='Minimum', evaluation_periods=int(config.get('cloudwatch', 'overrunning_threshold_minutes')), alarm_actions=[config.get('cloudwatch', 'topic_arn')])
    print 'Created Cloudwatch alarm for VulnPryer Pipeline'


# Builds the Vulnpryer Data Pipeline
def build_datapipeline():
    print '------------------------------------'
    print 'Building Vulnpryer Data Pipeline'
    print '------------------------------------'

    # Connect AWS Data Pipeline
    dp = boto.datapipeline.connect_to_region(region_name=config.get('general', 'pipeline_aws_region'), aws_access_key_id=config.get('general', 'aws_access_key_id'), aws_secret_access_key=config.get('general', 'aws_secret_access_key'))

    # Retrieve Data Pipeline ID by name
    search_marker = None
    while True:
        search_result = dp.list_pipelines(marker=search_marker)
        search_marker = search_result.get('marker')

        pipeline_ids = search_result.get('pipelineIdList')
        for i in range(0, len(pipeline_ids)):
            if pipeline_ids[i].get('name') == config.get('data_pipeline', 'pipeline_name'):
                print 'Pipeline with name ' + config.get('data_pipeline', 'pipeline_name') + ' has been found. Dropping pipeline...'
                dp.delete_pipeline(pipeline_ids[i].get('id'))
                break

        if not search_result.get('hasMoreResults'):
            break

    # Create new pipeline
    pipeline_id = dp.create_pipeline(config.get('data_pipeline', 'pipeline_name'),  config.get('data_pipeline', 'pipeline_name')).get('pipelineId')
    print 'Pipeline ' + config.get('data_pipeline', 'pipeline_name') + \
          ' with ID ' + pipeline_id + ' created on ' + \
          config.get('general', 'pipeline_aws_region')

    pipeline_objects = [config.get('data_pipeline', 'pipeline_schedule'),
                        config.get('data_pipeline', 'pipeline_resource'),
                        config.get('data_pipeline', 'pipeline_settings'),
                        config.get('data_pipeline', 'pipeline_alarm_success'),
                        config.get('data_pipeline', 'pipeline_alarm_failure'),
                        config.get('data_pipeline', 'pipeline_alarm_overrunning'),
                        config.get('data_pipeline', 'pipeline_vulnpryer_activity'),
                        config.get('data_pipeline', 'pipeline_overrunning_notification_activity')]

    pipeline_definition = ''
    for i in range(0, len(pipeline_objects)):
        pipeline_definition = pipeline_definition + prepare_pipeline_object(pipeline_objects[i])
        if i < len(pipeline_objects)-1:
            pipeline_definition = pipeline_definition + ','

    dp.put_pipeline_definition(ast.literal_eval('[' + pipeline_definition + ']'), pipeline_id)
    print 'Pipeline objects created'
    print 'Successfully built pipeline'


# ### MAIN #####
iam_status = define_iam_roles()
if not iam_status:
    print "Cannot proceed creating stack. Exiting.."
    exit(1)
instance_id = build_opsworks_stack()
if not instance_id:
    print "Cannot proceed building data pipeline. OpsWorks stack failed to create. Exiting.."
    exit(1)
prepare_custom_script(instance_id)
create_cloudwatch_alarm()
build_datapipeline()
exit(0)
