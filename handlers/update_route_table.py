import os
import sys
import boto3
import yaml
import botocore
import traceback
import peering_connection


def create_peering_route(vpc_data):
	"""
		Read input data to create/update route table within a vpc to forward traffic destined for peered vpc 

		Args:
			vpc_data: a dictionary of vpc parameters that contains cidr blocks, regions, route table ids, and vpc peering connection id
		Returns:
			'none'    
	"""

	# Extract vpc info parameters to create peering route
	requester_cidr_block = vpc_data['requester_cidr_block']
	accepter_cidr_block = vpc_data['accepter_cidr_block']
	requester_route_table_id = vpc_data['requester_route_table_id']
	accepter_route_table_id = vpc_data['accepter_route_table_id']
	vpc_peering_connection_id = vpc_data['peering_connection_id']
	requester_region = vpc_data['requester_region']
	accepter_region = vpc_data['accepter_region']

	# update requester route
	requester_ec2 = boto3.client('ec2', region_name=requester_region)
	requester_ec2.create_route(DestinationCidrBlock=accepter_cidr_block, RouteTableId=requester_route_table_id, VpcPeeringConnectionId=vpc_peering_connection_id)

	# update accepter route
	accepter_ec2 = boto3.client('ec2', region_name=accepter_region)
	accepter_ec2.create_route(DestinationCidrBlock=requester_cidr_block, RouteTableId=accepter_route_table_id, VpcPeeringConnectionId=vpc_peering_connection_id)
	return

def get_route_table_id(vpc_region, vpc_id):
	"""
		Read input data to get route table id within a specified vpc  

		Args:
			vpc_region: region to query for data
			vpc_id: ID of the associated VPC in the region
		Returns:
			All public route table available in the vpc    
	"""

	ec2 = boto3.client('ec2', region_name=vpc_region)
	response = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id','Values': [vpc_id]},{'Name': 'tag:aws:cloudformation:logical-id','Values': ['PublicRouteTable']}])
	pub_route_table_id = response['RouteTables'][0]['RouteTableId']
	return pub_route_table_id

def get_popped_configs(configs):
	"""
		Read input of loaded yaml configuration to iterate and parse data using .pop()

		Args:
		   config: dictionary containing parameter values to be read
		Returns:
		   popped list comprising of the second to last items in the config dictionary 
   """
	popped_config = configs.pop(0)
	return configs

def create_or_update_vpc_peering_route(configs):
	"""
		Read configuration list to either create or update peering connection route table using parameters in the list   

		Args:
			config: dictionary containing parameter values to be read
		Returns:
			dictionary containing - 
									'accepter_vpc_id'
									'requester_vpc_id' 
								    'peer_connection_id' 
								    'requester_route_table'
								    'requester_cidr_block'
								    'accepter_cidr_block' 
								    'accepter_region'
								    'accepter_route_table'
								    'requester_region' 
	"""
	route_configs = []

	try:
		for single_config in configs:

			# Extract vpc cidr block for each vpc to query for vpc peering connection info
			vpc_cidr_block = single_config['Parameters']['VPCCIDRBlock']
			print('cidr block of vpc = ' + vpc_cidr_block)

			# Extract region to setup boto3 client
			vpc_region = single_config['Region']
			print('Region to query vpc peering connection = ' + vpc_region)

			# Get vpc peering connection info
			ec2 = boto3.client('ec2', region_name=vpc_region)            
			vpc_peering_connections = ec2.describe_vpc_peering_connections(Filters=[{'Name': 'requester-vpc-info.cidr-block','Values': [vpc_cidr_block]}])

			# Create peering connection info dictionary and update route table
			for vpc_info in vpc_peering_connections['VpcPeeringConnections']:
				vpc_data = {}
				vpc_data['accepter_vpc_id'] = vpc_info['AccepterVpcInfo']['VpcId']
				vpc_data['requester_vpc_id'] = vpc_info['RequesterVpcInfo']['VpcId']
				vpc_data['accepter_cidr_block'] = vpc_info['AccepterVpcInfo']['CidrBlockSet'][0]['CidrBlock']
				vpc_data['requester_cidr_block'] = vpc_info['RequesterVpcInfo']['CidrBlockSet'][0]['CidrBlock']
				vpc_data['accepter_region'] = vpc_info['AccepterVpcInfo']['Region']
				vpc_data['requester_region'] = vpc_info['RequesterVpcInfo']['Region']
				vpc_data['accepter_route_table_id'] = get_route_table_id(vpc_data['accepter_region'], vpc_data['accepter_vpc_id'])
				vpc_data['requester_route_table_id'] = get_route_table_id(vpc_data['requester_region'], vpc_data['requester_vpc_id'])
				vpc_data['peering_connection_id'] = vpc_info['VpcPeeringConnectionId']
				
				# Update route for both requester and accepter peering connection
				create_peering_route(vpc_data)
				route_configs.append(vpc_data)		
			return route_configs

	except Exception as e:
		# If any other exceptions which we didn't expect are raised
		# then fail the dictionary creation and log the exception message.
		print('Function failed due to exception.')
		print(e)
		traceback.print_exc()
		print('Function exception: ' + str(e))

def main():
	# Define global variables
	CONFIGS=sys.argv[1]

	try:
		# Load user defined configuration yaml file
		setup_data = peering_connection.load_yaml_file(CONFIGS) 
		# vpc_region_keypairs = peering_connection.get_vpc_ids(CONFIGS)

		# Create a clone of the user configuration and update peering route table
		setup_data_clone = list(setup_data)
		print(create_or_update_vpc_peering_route(setup_data_clone))

		# iterate through rest of the cloned list to update route for remaining requester and accepter vpcs
		for i in range(1, len(setup_data_clone)):
			configs = get_popped_configs(setup_data_clone)
			setup_data_clone = list(configs)
			if len(configs) < 1:
				break
			print(create_or_update_vpc_peering_route(configs))

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
