# OpenStackSDK
This repository contains a set of scripts for testing out the OpenStackSDK (Python).

Information about the SDK can be found in the following links:
  - Github: https://github.com/openstack/python-openstacksdk
  - OpenStack: http://developer.openstack.org/sdks/python/openstacksdk/users/index.html

The SDK can easily be installed using pip: `pip install openstacksdk`

## Fractals Application Using the SDK
A tutorial for deploying your [first OpenStack application](http://developer.openstack.org/firstapp-libcloud/getting_started.html) (Fractals application) is available. However, it uses the [Apache libcloud Python SDK](https://libcloud.apache.org/).

**This repository aims to achieve the same functionality demonstrated in the tutorial, but with the OpenstackSDK.**

## Repository Contents

### fractals.py
This script constitutes the *[Getting Started](http://developer.openstack.org/firstapp-libcloud/getting_started.html)* part of the tutorial.

The script creates a connection to the Identity endpoint and proceeds to create an instance that install the Fractals application. The script also creates and assigns a Floating IP to this instance so that it can be accessed through the browser as well as through SSH (using an existing Keypair).

### micro_fractals.py
This script proceeds to the *[Introduction to the fractals application architecture](http://developer.openstack.org/firstapp-libcloud/introduction.html)* part of the tutorial, which focuses on separating the architecture into micro services as well as implementing scalability and automation characteristics for the Fractals application.

To achieve this, the script creates two instances. A **controller instance**, which is in charge of hosting the API, database, and messaging services; and a **worker instance**, which is in charge of generating the fractals.

This script creates two **security groups** along with rules for each group. One security group is for the services that run on the **worker node**, and the other for the services that run on the **controller** node.

Also, this script proceeds to create a new *demokey* keypair if it does not exist. Floating IPs are created and assigned to each instance so that they can be accessed through SSH.

