from openstack import connection
from openstack import profile
from openstack import utils
from openstack import compute

import sys
import os
import base64

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

auth_args = {
    'auth_url': 'http://100.67.130.148:5000/v2.0',
    'project_name': 'admin',
    'username': 'admin',
    'password': 'admin',
}

conn = connection.Connection(**auth_args)

IMAGE_NAME = 'ubuntu14.04'
FLAVOR_NAME = 'm1.small'
NETWORK_NAME = 'private'
KEYPAIR_NAME = 'default'
PUBLIC_NETWORK_NAME = 'public'

image = conn.compute.find_image(IMAGE_NAME)
flavor = conn.compute.find_flavor(FLAVOR_NAME)

# By default, OpenStack filters all traffic. You must create a security group and apply it to your
# instance. The security group allows HTTP and SSH access.
network = conn.network.find_network(NETWORK_NAME)
public_network = conn.network.find_network(PUBLIC_NETWORK_NAME)

# Keypair allows us to access the instance. You must import an SSH publickey into OpenStack to create
# a jey pair. OpenStack installs this key pair on the new instance. Typically, the key pair is written
# to '.ssh/id_rsa.pub'
keypair = conn.compute.find_keypair(KEYPAIR_NAME)

"""
print "Image:"
print(image)
print

print "Flavor:"
print(flavor)
print

print "Network:"
print(network)
print

print "Keypair:"
print(keypair)
print
"""

# Create a keypair if there isn't one available, using the SDK
#keypair = create_keypair(conn)


# Check for Security Groups
print "Checking for existing security group..."
security_group_name = 'all-in-one'
security_group_exists = False
for security_group in conn.network.security_groups():
    if security_group.name == security_group_name:
        all_in_one_security_group = security_group
        security_group_exists = True

if security_group_exists:
    print("Security Group " + all_in_one_security_group.name + " already exists. Skipping creation.")
    print


# At minimum, a server requires a name, an image, a flavor, and a network on creation.
# Ideally, you'll also create a server using a keypair so you can login to that server
# with the private key.
print "Checking for existing instance..."
SERVER_NAME = 'sdk_server'

udata = '''#!/usr/bin/env bash
curl -L -s https://git.openstack.org/cgit/openstack/faafo/plain/contrib/install.sh | bash -s -- \
    -i faafo -i messaging -r api -r worker -r demo
'''

instance_exists = False

for instance in conn.compute.servers():
    if instance.name == SERVER_NAME:
        server = instance
        instance_exists = True

if instance_exists:
    print("Instance " + server.name + " already exists. Skipping creation.")
    print
else:
    server = conn.compute.create_server(
        name=SERVER_NAME, image_id=image.id, flavor_id=flavor.id,
        networks=[{"uuid": network.id}], key_name=keypair.name, user_data=base64.b64encode(udata), security_group=security_group_name)

    # Servers take time to boot, so we call 'wait_for_server' to wait for it to become active.
    print 'Instance not found. Creating new instance...'
    server = conn.compute.wait_for_server(server)
    print bcolors.OKGREEN + "Instance " + SERVER_NAME + " created." + bcolors.ENDC
    print



# Associate a floating IP for external connectivity
# =================================================
#
# By default, the instance has outbound network access. To make the instance reachable from the
# Internet, you need an IP address. By default, in some cases, the instance is provisioned
# with a publicly rout-able IP address. In this case, you see an IP address listed under
# public_ips or private_ips when you list the instances. If not, you must create and attach a
# floating IP address to the instance.


# Check whether a private IP address is assigned to the instance.
# If one is assigned, users can use this address to access the instance on some OpenStack clouds.
private_ip = None
if 'private' in server.addresses:
    private_ip = server.addresses['private'][0]
    print("Private IP found: {}".format(private_ip['addr']))
    print

# Determine whether a public IP address is assigned to the instance
# If one is assigned, users can use this address to access the instance.
public_ip = None
if 'public' in server.addresses:
    public_ip = server.addresses['public'][0]
    print("Public IP found: {}".format(public_ip['addr']))
    print

# Check if instance has Floating IP
floating_ip = None
for ip in server.addresses['private']:
    if ip['OS-EXT-IPS:type'] == 'floating':
        floating_ip = ip
        print("Floating IP found: {}".format(floating_ip['addr']))
        print
        break


if public_ip:
    print("Instance " + SERVER_NAME + " already has a public ip. Skipping attachment.")
    print
elif floating_ip:
    print("Instance " + SERVER_NAME + " already has a floating ip. Skipping creation.")
    print
else:
    # Attach the Floating IP to the instance
    print "Creating Floating IP for instance..."
    floating_ip = create_floating_ip(server, public_network)
    print bcolors.OKGREEN + "Floating IP " + floating_ip.floating_ip_address + " created an assigned to " + SERVER_NAME + bcolors.ENDC
    print

actual_ip_address = None

if public_ip:
    actual_ip_address = public_ip['addr']
elif floating_ip:
    try:
        actual_ip_address = floating_ip['addr']
    except Exception as e:
        actual_id_address = floating_ip.floating_ip_address
elif private_ip:
    actual_ip_address = private_ip['addr']

print(bcolors.OKGREEN + "The Fractals application will be deployed to http://{}".format(actual_ip_address) + bcolors.ENDC)
