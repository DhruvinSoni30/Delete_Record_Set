import boto3
import argparse

parser = argparse.ArgumentParser(description="Parameters")

parser.add_argument("-r", "--region", type=str, help="Region")
parser.add_argument("-p", "--pod_names", type=str, help="Pod Names")
parser.add_argument("-i", "--hosted_zone_id", type=str, help="Hosted Zone ID")

args = parser.parse_args()

region = args.region
region = str(region)

pod_names = args.pod_names.split(',')
pod_names = str(pod_names)

hosted_zone_id =  args.hosted_zone_id
hosted_zone_id = str(hosted_zone_id)

aws_region = region

# Initialize Boto3 clients for EC2 and Route 53
ec2_client = boto3.client('ec2', region_name=aws_region)
route53_client = boto3.client('route53', region_name=aws_region)

# Read the list of EC2 instance names 
for pod_name in pod_names:

    # List EC2 instances
    response = ec2_client.describe_instances()
    ec2_instances = [instance for reservation in response['Reservations'] for instance in reservation['Instances']]

for ec2_instance in ec2_instances:
    instance_name = None

    # Find the EC2 instance name by looking at tags or other metadata
    for tag in ec2_instance.get('Tags', []):
        if tag['Key'] == 'Name':
            instance_name = tag['Value']

    response = ec2_client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': [instance_name]}])

    if 'Reservations' in response:
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                # Get the instance's private IP address
                public_ip = instance['PublicIpAddress']

                # List Route 53 resource record sets in your hosted zone
                hosted_zone_id = hosted_zone_id  # Replace with your hosted zone ID
                response = route53_client.list_resource_record_sets(HostedZoneId=hosted_zone_id)

                for record_set in response['ResourceRecordSets']:
                    # Check for A and CNAME records associated with the EC2 instance's private IP
                    if record_set['Type'] in ['A', 'CNAME'] and record_set['ResourceRecords'][0]['Value'] == public_ip:
                        # Delete the record
                        route53_client.change_resource_record_sets(
                            HostedZoneId=hosted_zone_id,
                            ChangeBatch={
                                'Changes': [
                                    {
                                        'Action': 'DELETE',
                                        'ResourceRecordSet': record_set
                                    }
                                ]
                            }
                        )
                        print(f"Deleted {record_set['Type']} record: {record_set['Name']}")
