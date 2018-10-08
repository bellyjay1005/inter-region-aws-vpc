import os
import sys
import boto3
import yaml
import botocore
import traceback
from boto3.session import Session

ec2 = boto3.client('ec2')

def establish_vpc_connetion(requester_vpc_id, accepter_vpc_id, peer_region)
	response = ec2.create_vpc_peering_connection(PeerVpcId=peer_vpc_id, VpcId='string', PeerRegion='string')
	connection_status = response['VpcPeeringConnection'][3]['Status'][0]['Code']
	return connection_status