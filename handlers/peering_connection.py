import os
from time import sleep
import sys
import boto3
import yaml
import botocore
import traceback
from deploy import vpc_deployment_manager
from deploy import load_yaml_file

def get_vpc_ids(configs):
	"""
		Read input configuration file that contains stack creation arguments and parameters
		This function describes created vpc resource id.

		Args:
			config: dictionary containing parameter values to be read
		Returns:
			List of vpc id and residing region key-pair    
	"""
	setup_data = load_yaml_file(configs)
	vpc_id_list = []

	for single_setup_data in setup_data:

		# Extract region to query physical resources id
		vpc_region = single_setup_data['Region']
		print('Region to query vpc id = ' + vpc_region)

		# Extract the vpc name and region and create a stack name
		vpc_name = single_setup_data['vpc_name']
		stack_name = vpc_region+'-'+vpc_name
		print ('Stack name of vpc to query = ' + stack_name)

		# Get vpc id for specified stackname
		cfn = boto3.client('cloudformation', region_name=vpc_region)	         
		response = cfn.describe_stack_resource(StackName=stack_name, LogicalResourceId='VPC')
		vpc_id = response['StackResourceDetail']['PhysicalResourceId']
		print ('VPC ID for deployed vpc = ' + vpc_id)

		# Create vpc-id and region key-value pairs
		keypair = {}
		keypair['VPCID'] = vpc_id
		keypair['REGION'] = vpc_region
		vpc_id_list.append(keypair)

	return vpc_id_list

def request_vpc_peering_connection(accepter_vpc_id, requester_vpc_id, accepter_region, requester_region):
	"""
		Read input data of vpc id and corresponding region to initiate peering 
		connection with another vpc using vpc id and associated region 

		Args:
			accepter_vpc_id: vpc id of the requesting vpc
			requester_vpc_id: vpc id of the accepting vpc
			accepter_region: The region of the accepting vpc
			requester_region: The region you making the request (default)
		Returns:
			Id of the peering connection    
	"""
	ec2 = boto3.client('ec2', region_name=requester_region)
	response = ec2.create_vpc_peering_connection(VpcId=requester_vpc_id, PeerVpcId=accepter_vpc_id, PeerRegion=accepter_region)
	PeeringConnectionId = response['VpcPeeringConnection']['VpcPeeringConnectionId']
	return PeeringConnectionId

def accept_vpc_peering_connection(PeeringConnectionId, accepter_region):
	"""
		Read input data of established vpc peering connection and 
		corresponding region of the accepting vpc

		Args:
			PeeringConnectionId: Id of the peering connection
			accepter_region: The region of the accepting vpc
		Returns:
			peering connection status code    
	"""
	ec2 = boto3.client('ec2', region_name=accepter_region)
	response = ec2.accept_vpc_peering_connection(VpcPeeringConnectionId=PeeringConnectionId)
	connection_status = response['VpcPeeringConnection']['Status']['Code']
	return connection_status

def get_pairing_config(vpc_region_keypairs):
	"""
		Read input of vpc id and region for creating peering connection

		Args:
		   vpc_region_keypairs: vpc id and region pair
		Returns:
		   First item in the above list and a concatenated list
		   comprising of the second to end items 
   """
	popped_vpc = vpc_region_keypairs.pop(0)
	return [popped_vpc, vpc_region_keypairs]

def establish_vpc_connection(main_vpc, pairing_vpcs):
	"""
		Read configuration list with a popped item and a concatenated list
		comprising of the second to end items   

		Args:
			main_vpc: first vpc_id_region keypair
			pairing_vpcs: The rest of the vpc_id_region-keypair in the input list
		Returns:
			peering connection id and status code of connection    
	"""
	connection_state = []   
	requester_region = main_vpc['REGION']
	requester_vpc_id = main_vpc ['VPCID']

	for vpc in pairing_vpcs:
		accepter_region = vpc['REGION']
		accepter_vpc_id = vpc ['VPCID']

		peering_connection_id = request_vpc_peering_connection(accepter_vpc_id, requester_vpc_id, accepter_region, requester_region)

		# wait for peering lifecycle to transition from 'provisioning' to 'active'
		sleep(5)
		
		peering_connection_status = accept_vpc_peering_connection(peering_connection_id, accepter_region)
		status = {}
		status['Connection ID'] = peering_connection_id
		status['Status'] = peering_connection_status
		connection_state.append(status)
	return connection_state

def main():
	# Define global variables
	CONFIGS=sys.argv[1]

	try:
		# Create a list of vpc_id with region pair 
		vpc_region_keypairs = get_vpc_ids(CONFIGS)

		# Create a clone list to work with
		vpc_region_keypairs_clone = list(vpc_region_keypairs)

		# iterate through the cloned list to establish peering connection
		for i in range(1, len(vpc_region_keypairs)):
			main_vpc, pairing_vpcs = get_pairing_config(vpc_region_keypairs_clone)
			vpc_region_keypairs_clone = list(pairing_vpcs)
			if len(pairing_vpcs) < 1:
				break
			print(establish_vpc_connection(main_vpc, pairing_vpcs))

	except Exception as e:
		# If any other exceptions which we didn't expect are raised
		# then fail the query and log the exception message.
		print('Function failed due to exception.')
		print(e)
		traceback.print_exc()
		print('Function exception: ' + str(e))

	print('VPC Peering Connection Complete.')
	return "Complete."

if __name__ =="__main__":
   main()
