from openstack import connection
from openstack import profile
from openstack import utils
from openstack import compute

import sys
import os
import errno
import base64
import time

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def _get_server_port(server):
    for port in conn.network.ports():
        for ip in port.fixed_ips:
            if ip.get("subnet_id") == conn.network.find_network(server.addresses.keys()[0])['subnets'][0] and ip.get("ip_address") == server.addresses.get(server.addresses.keys()[0])[0]['addr']:
                return port

def create_floating_ip(server, external_network):
    server_fixed_ip_address = server.addresses.get(server.addresses.keys()[0])[0]['addr']
    for ip in conn.network.ips():
        if ip.fixed_ip_address == None:
            server_port = _get_server_port(server)
            return conn.network.update_ip(ip, fixed_ip_address=server_fixed_ip_address, port_id=server_port.id)
    server_port = _get_server_port(server)
    return conn.network.create_ip(floating_network_id=external_network.id,
                                  fixed_ip_address=server_fixed_ip_address,
                                  port_id=server_port.id)


def delete_security_group_rules(security_group):
    # Deletes all rules from this security group
    for rule in security_group.security_group_rules:
        conn.network.delete_security_group_rule(rule['id'])


auth_args = {
    'auth_url': 'http://100.67.130.148:5000/v2.0',
    'project_name': 'admin',
    'username': 'admin',
    'password': 'admin',
}

conn = connection.Connection(**auth_args)


image = conn.compute.find_image('ubuntu14.04')
flavor = conn.compute.find_flavor('m1.small')
network = conn.network.find_network('private')
keypair = conn.compute.find_keypair('demokey')
#keypair = None
public_network = conn.network.find_network('public')


## Create API Services security group
print "Creating API security group..."
api_group = conn.network.create_security_group(name='api', description='for API services only')

# Create rules for API security group
print "Creating security group rule #1 for 'api'..."
api_group_rule1 = {
        'direction': 'ingress',
        'remote_ip_prefix': '',
        'protocol': 'tcp',
        'port_range_min': '80',
        'port_range_max': '80',
        'security_group_id': api_group.id,
        'ethertype': 'IPv4'
    }
conn.network.create_security_group_rule(**api_group_rule1)

print "Creating security group rule #2 for 'api'..."
api_group_rule2 = {
        'direction': 'ingress',
        'remote_ip_prefix': '',
        'protocol': 'tcp',
        'port_range_min': '22',
        'port_range_max': '22',
        'security_group_id': api_group.id,
        'ethertype': 'IPv4'
    }
conn.network.create_security_group_rule(**api_group_rule2)

print

##  Create Worker security group
print "Creating worker Security Group..."
worker_group = conn.network.create_security_group(name='worker', description='for services that run on worker node')

# Create security group rule
worker_group_rule = {
    'direction': 'ingress',
    'remote_ip_prefix': '',
    'protocol': 'tcp',
    'port_range_min': '22',
    'port_range_max': '22',
    'security_group_id': worker_group.id,
    'ethertype': 'IPv4'
}

print "Creating security group rule for 'worker'..."
conn.network.create_security_group_rule(**worker_group_rule)

print

## Create Controller security group
print "Creating security group 'control'..."
controller_group = conn.network.create_security_group(name='control', description='for services that run on a control node')

controller_group_rule1 = {
    'direction': 'ingress',
    'remote_ip_prefix': '',
    'protocol': 'tcp',
    'port_range_min': '22',
    'port_range_max': '22',
    'security_group_id': controller_group.id,
    'ethertype': 'IPv4'
}
print "Creating security group rule #1 for 'control'..."
conn.network.create_security_group_rule(**controller_group_rule1)

controller_group_rule2 = {
    'direction': 'ingress',
    'remote_ip_prefix': '',
    'protocol': 'tcp',
    'port_range_min': '80',
    'port_range_max': '80',
    'security_group_id': controller_group.id,
    'ethertype': 'IPv4'
}
print "Creating security group rule #2 for 'control'..."
conn.network.create_security_group_rule(**controller_group_rule2)

controller_group_rule3 = {
    'direction': 'ingress',
    'remote_ip_prefix': '',
    'remote_group_id': worker_group.id,
    'protocol': 'tcp',
    'port_range_min': '5672',
    'port_range_max': '5672',
    'security_group_id': controller_group.id,
    'ethertype': 'IPv4'
}
print "Creating security group rule #3 for 'control'..."
conn.network.create_security_group_rule(**controller_group_rule3)


print

## Create Services security group
print "Creating security group 'services'..."
services_group = conn.network.create_security_group(name='services', description='for DB and AMQP services only')

services_group_rule1 = {
    'direction': 'ingress',
    'remote_ip_prefix': '',
    'protocol': 'tcp',
    'port_range_min': '22',
    'port_range_max': '22',
    'security_group_id': services_group.id,
    'ethertype': 'IPv4'
}
print "Creating security group rule #1 for 'services'..."
conn.network.create_security_group_rule(**services_group_rule1)

services_group_rule2 = {
    'direction': 'ingress',
    'remote_ip_prefix': '',
    'remote_group_id': api_group.id,
    'protocol': 'tcp',
    'port_range_min': '3306',
    'port_range_max': '3306',
    'security_group_id': services_group.id,
    'ethertype': 'IPv4'
}
print "Creating security group rule #2 for 'services'..."
conn.network.create_security_group_rule(**services_group_rule2)

services_group_rule3 = {
    'direction': 'ingress',
    'remote_ip_prefix': '',
    'remote_group_id': worker_group.id,
    'protocol': 'tcp',
    'port_range_min': '5672',
    'port_range_max': '5672',
    'security_group_id': services_group.id,
    'ethertype': 'IPv4'
}
print "Creating security group rule #3 for 'services'..."
conn.network.create_security_group_rule(**services_group_rule3)

services_group_rule4 = {
    'direction': 'ingress',
    'remote_ip_prefix': '',
    'remote_group_id': api_group.id,
    'protocol': 'tcp',
    'port_range_min': '5672',
    'port_range_max': '5672',
    'security_group_id': services_group.id,
    'ethertype': 'IPv4'
}
print "Creating security group rule #4 for 'services'..."
conn.network.create_security_group_rule(**services_group_rule4)

print

### Split the database and message queue ###

# Before you scale out your application services, like the API service or the workers,
# you must add a central database and an app-services messaging instance.
# The database and messaging queue will be used to track the state of fractals
# and to coordinate the communication between the services.

userdata = '''#!/usr/bin/env bash
curl -L -s http://git.openstack.org/cgit/openstack/faafo/plain/contrib/install.sh | bash -s -- \
    -i database -i messaging
'''

print "Creating 'services' instance...\n"
instance_services = conn.compute.create_server(
        name = 'app-services',
        image_id = image.id,
        flavor_id = flavor.id,
        networks=[{"uuid": network.id}],
        key_name = keypair.name,
        user_data = base64.b64encode(userdata),
        security_group = services_group.name
    )

instance_services = conn.compute.wait_for_server(instance_services)
services_ip = instance_services.addresses['private'][0] # Private IP

### Scale the API service ###

# With multiple workers producing fractals as fast as they can, the system must be able to receive
# the requests for fractals as quickly as possible. If our application becomes popular,
# many thousands of users might connect to our API to generate fractals.

# Armed with a security group, image, and flavor size, you can add multiple API services:

userdata = '''#!/usr/bin/env bash
curl -L -s http://git.openstack.org/cgit/openstack/faafo/plain/contrib/install.sh | bash -s -- \
    -i faafo -r api -m 'amqp://guest:guest@%(services_ip)s:5672/' \
    -d 'mysql+pymysql://faafo:password@%(services_ip)s:3306/faafo'
''' % { 'services_ip': services_ip }

print "Creating API 1 instance..."
instance_api_1 = conn.compute.create_server(
        name = 'app-api-1',
        image_id = image.id,
        flavor_id = flavor.id,
        networks=[{"uuid": network.id}],
        key_name = keypair.name,
        user_data = base64.b64encode(userdata),
        security_group = api_group.name
    )

instance_api_1 = conn.compute.wait_for_server(instance_api_1)
api_1_ip = instance_api_1.addresses['private'][0]

print "Creating API 2 Instance..."
instance_api_2 = conn.compute.create_server(
        name = 'app-api-2',
        image_id = image.id,
        flavor_id = flavor.id,
        networks=[{"uuid": network.id}],
        key_name = keypair.name,
        user_data = base64.b64encode(userdata),
        security_group = api_group.name
    )

instance_api_2 = conn.compute.wait_for_server(instance_api_2)
api_2_ip = instance_api_2.addresses['private'][0]

for instance in [instance_api_1, instance_api_2]:
    floating_ip = create_floating_ip(instance, public_network)
    print bcolors.OKBLUE + "Allocated Floating IP " + floating_ip.floating_ip_address + " to " + instance.name + bcolors.ENDC


print

### Scale the workers ###

# To increase overall capacitty, add 3 workers:

userdata = '''#!/usr/bin/env bash
curl -L -s http://git.openstack.org/cgit/openstack/faafo/plain/contrib/install.sh | bash -s -- \
    -i faafo -r worker -e 'http://%(api_1_ip)s' -m 'amqp://guest:guest@%(services_ip)s:5672/'
''' % {'api_1_ip': api_1_ip, 'services_ip': services_ip}

print "Creating worker 1 instance..."
instance_worker_1 = conn.compute.create_server(
        name = 'app-worker-1',
        image_id = image.id,
        flavor_id = flavor.id,
        networks=[{"uuid": network.id}],
        key_name = keypair.name,
        #user_data = base64.b64encode(userdata),
        security_group = worker_group.name
    )
instance_worker_1 = conn.compute.wait_for_server(instance_worker_1)

print "Creating worker 2 instance..."
instance_worker_2 = conn.compute.create_server(
        name = 'app-worker-2',
        image_id = image.id,
        flavor_id = flavor.id,
        networks=[{"uuid": network.id}],
        key_name = keypair.name,
        user_data = base64.b64encode(userdata),
        security_group = worker_group.name
    )

instance_worker_2 = conn.compute.wait_for_server(instance_worker_2)

print "Creating worker 3 instance..."
instance_worker_3 = conn.compute.create_server(
        name = 'app-worker-3',
        image_id = image.id,
        flavor_id = flavor.id,
        networks=[{"uuid": network.id}],
        key_name = keypair.name,
        user_data = base64.b64encode(userdata),
        security_group = worker_group.name
    )

instance_worker_3 = conn.compute.wait_for_server(instance_worker_3)

print
