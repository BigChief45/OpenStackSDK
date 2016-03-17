from openstack import connection
from openstack import profile
from openstack import utils
from openstack import compute

import sys
import os
import errno
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
#keypair = conn.compute.find_keypair('demokey')
keypir = None
public_network = conn.network.find_network('public')

# Check if Keypair exists
print "Checking for existing keypair 'sdkkey'..."
keypair_name = 'demokey'
pub_key_file = '~/.ssh/id_rsa.pub'
keypair_exists = False
for key in conn.compute.keypairs():
    if key.name == keypair_name:
        keypair = key
        keypair_exists = True


if keypair_exists:
    print bcolors.WARNING + "Keypair " + keypair_name + " already exists. Skipping import." + bcolors.ENDC
else:
    # Create the keypair
    print "Keypair 'sdkkey' does not exist."
    print "Creating keypair '" + keypair_name + "'..."
    keypair = conn.compute.create_keypair(name=keypair_name)

    # Try creating the directory if it doesn't exist
    HOME_DIR = os.path.expanduser("~")
    SSH_DIR = HOME_DIR + '/.ssh'
    PRIVATE_KEYPAIR_FILE = SSH_DIR + 'id_rsa.' + keypair_name
    try:
        os.mkdir(SSH_DIR)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e

    # Write the key to the ssh key file
    with open(PRIVATE_KEYPAIR_FILE, 'w') as f:
        f.write("%s" % keypair.private_key)

    os.chmod(PRIVATE_KEYPAIR_FILE, 0o400)


print

# Check if worker security group exists
print "Checking for existing security group 'worker'..."
security_group_exists = False
worker_group = None
for security_group in conn.network.security_groups():
    if security_group.name == 'worker':
        worker_group = security_group
        security_group_exists = True
        break

if security_group_exists:
    print bcolors.WARNING + "WARNING: Security group 'worker' exists." + bcolors.ENDC
    print "Deleting security group 'worker'..."

    # First, delete its security group rules
    delete_security_group_rules(worker_group)

    conn.network.delete_security_group(worker_group)
else:
    print "Security Group does not exist. Creating security group 'worker'..."
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

# Check if control security group exists
print "Checking for existing security group 'control'..."
controller_group = None
security_group_exists = False
for security_group in conn.network.security_groups():
    if security_group.name == 'control':
        controller_group = security_group
        security_group_exists = True
        break

if security_group_exists:
    print bcolors.WARNING + "WARNING: Security group 'control' exists." + bcolors.ENDC
    print "Deleting security group 'control'..."

    # First delete the group's rules
    delete_security_group_rules(controller_group)

    conn.network.delete_security_group(controller_group)
else:
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

udata = '''#!/usr/bin/env bash
curl -L -s http://git.openstack.org/cgit/openstack/faafo/plain/contrib/install.sh | bash -s -- \
    -i messaging -i faafo -r api
'''

# Check if controller instance exists
instance_exists = False
instance_controller_1 = None
for instance in conn.compute.servers():
    if instance.name == 'app-controller':
        instance_controller_1 = instance
        instance_exists = True

if instance_exists:
    print bcolors.WARNING + "WARNING: Instance 'app-controller' already exists. Skipping creation." + bcolors.ENDC
else:
    print "Instance 'app-controller' not found. Creating new instance 'app-controller'..."

    instance_controller_1 = conn.compute.create_server(
        name = 'app-controller',
        image_id = image.id,
        flavor_id = flavor.id,
        networks=[{"uuid": network.id}],
        key_name = keypair.name,
        user_data = base64.b64encode(udata),
        security_group = controller_group.name
    )

    instance_controller_1 = conn.compute.wait_for_server(instance_controller_1)

    print bcolors.OKGREEN + "Instance 'app-controller' created." + bcolors.ENDC

print

## Check for a floating IP
floating_ip = None
for ip in instance_controller_1.addresses['private']:
    if ip['OS-EXT-IPS:type'] == 'floating':
        floating_ip = ip
        print("Floating IP found: {}".format(floating_ip['addr']))
        break

if floating_ip:
    print("Instance " + instance_controller_1.name + " already has a floating ip. Skipping creation.")
    floating_ip_address = floating_ip['addr']
else:
    # Create and Attach the Floating IP to the instance
    print "Creating Floating IP for instance 'app-controller'..."
    new_floating_ip = create_floating_ip(instance_controller_1, public_network)
    floating_ip_address = new_floating_ip.floating_ip_address
    print bcolors.OKGREEN + "Floating IP " + floating_ip_address + " created and assigned to " + instance_controller_1.name + bcolors.ENDC

print

print "Application will be deployed to http://%s" % floating_ip_address
print


## CREATE THE WORKER INSTANCE

ip_controller = floating_ip_address

userdata = '''#!/usr/bin/env bash
curl -L -s http://git.openstack.org/cgit/openstack/faafo/plain/contrib/install.sh | bash -s -- \
    -i faafo -r worker -e 'http://%(ip_controller)s' -m 'amqp://guest:guest@%(ip_controller)s:5672/'
''' % {'ip_controller': ip_controller}

# Check if the worker instance  already exists
instance_exists = False
instance_worker_1 = None
for instance in conn.compute.servers():
    if instance.name == 'app-worker-1':
        instance_worker_1 = instance
        instance_exists = True

if instance_exists:
    print bcolors.WARNING + "WARNING: Instance 'app-worker-1' already exists. Skipping creation." + bcolors.ENDC
else:
    print "Instance 'app-worker-1' not found. Creating new instance 'app-worker-1'..."

    instance_worker_1 = conn.compute.create_server(
        name = 'app-worker-1',
        image_id = image.id,
        flavor_id = flavor.id,
        networks=[{"uuid": network.id}],
        key_name = keypair.name,
        user_data = base64.b64encode(udata),
        security_group = worker_group.name
    )

    instance_worker_1 = conn.compute.wait_for_server(instance_worker_1)

    print bcolors.OKGREEN + "Instance 'app-worker-1' created." + bcolors.ENDC

print


## Check for a floating IP for worker instance
floating_ip = None
for ip in instance_worker_1.addresses['private']:
    if ip['OS-EXT-IPS:type'] == 'floating':
        floating_ip = ip
        print("Floating IP found: {}".format(floating_ip['addr']))
        break

if floating_ip:
    print("Instance " + instance_worker_1.name + " already has a floating ip. Skipping creation.")
    floating_ip_address = floating_ip['addr']
else:
    # Create and Attach the Floating IP to the instance
    print "Creating Floating IP for instance 'app-worker-1'..."
    new_floating_ip = create_floating_ip(instance_worker_1, public_network)
    floating_ip_address = new_floating_ip.floating_ip_address
    print bcolors.OKGREEN + "Floating IP " + floating_ip_address + " created and assigned to " + instance_worker_1.name + bcolors.ENDC

print

print "The worker will be available for SSH at %s" % floating_ip_address
