from openstack import connection
from openstack import profile
from openstack import utils
from openstack import compute
import sys
import os

auth_args = {
    'auth_url': '$[IDENTITY_ENDPOINT]',
    'project_name': 'admin',
    'username': 'admin',
    'password': 'admin',
}

conn = connection.Connection(**auth_args)

IMAGE_NAME = 'ubuntu14.04'
FLAVOR_NAME = 'm1.small'
NETWORK_NAME = 'private'
KEYPAIR_NAME = 'default'

image = conn.compute.find_image(IMAGE_NAME)
flavor = conn.compute.find_flavor(FLAVOR_NAME)

# By default, OpenStack filters all traffic. You must create a security group and apply it to your
# instance. The security group allows HTTP and SSH access.
network = conn.network.find_network(NETWORK_NAME)

# Keypair allows us to access the instance. You must import an SSH publickey into OpenStack to create
# a jey pair. OpenStack installs this key pair on the new instance. Typically, the key pair is written
# to '.ssh/id_rsa.pub'
keypair = conn.compute.find_keypair(KEYPAIR_NAME)

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
        networks=[{"uuid": network.id}], key_name=keypair.name)

    # Servers take time to boot, so we call 'wait_for_server' to wait for it to become active.
    server = conn.compute.wait_for_server(server)


# Destroy an instance/server
#server = conn.compute.find_server('sdk_server')
#print "Destroying server..."
#conn.compute.delete_server(server)

# During instance creation, you can provide userdata to OpenStack to configure instances after
# they boot.
#userdata = ''


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
    print("Private IP found: {}".format(private_ip))

# Determine whether a public IP address is assigned to the instance
# If one is assigned, users can use this address to access the instance.
public_ip = None
if 'public' in server.addresses:
    public_ip = server.addresses['public'][0]
    print("Public IP found: {}".format(public_ip))


# Find an available Floating IP
print "Finding an available Floating IP..."
unused_floating_ip = None
for floating_ip in conn.network.ips():
    print(floating_ip)
    # floating_ip.node_id ???
    if not floating_ip:
        unused_floating_ip = floating_ip
        break

# Allocate this pool to the project and use it to get a floating IP address
if not unused_floating_ip:
    pool = conn.network.pools()[0]
    print('Allocating new Floating IP from pool: {}'.format(pool))
    #unused_floating_ip = pool.create_floating_ip()

if public_ip:
    print("Instance " + SERVER_NAME + " already has a public ip. Skipping attachment.")
else:
