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

### [fractals.py](https://github.com/BigChief45/OpenStackSDK/blob/master/fractals.py)
This script constitutes the *[Getting Started](http://developer.openstack.org/firstapp-libcloud/getting_started.html)* part of the tutorial.

The script creates a connection to the Identity endpoint and proceeds to create an instance that install the Fractals application. The script also creates and assigns a Floating IP to this instance so that it can be accessed through the browser as well as through SSH (using an existing Keypair).

### [micro_fractals.py](https://github.com/BigChief45/OpenStackSDK/blob/master/micro_fractals.py)
This script proceeds to the *[Introduction to the fractals application architecture](http://developer.openstack.org/firstapp-libcloud/introduction.html)* part of the tutorial, which focuses on separating the architecture into micro services as well as implementing scalability and automation characteristics for the Fractals application.

To achieve this, the script creates two instances. A **controller instance**, which is in charge of hosting the API, database, and messaging services; and a **worker instance**, which is in charge of generating the fractals.

This script creates two **security groups** along with rules for each group. One security group is for the services that run on the **worker node**, and the other for the services that run on the **controller** node.

Also, this script proceeds to create a new *demokey* keypair if it does not exist. Floating IPs are created and assigned to each instance so that they can be accessed through SSH.

### scaling_fractals.py

This script proceeds in to the *[Scaling Out](http://developer.openstack.org/firstapp-libcloud/scaling_out.html)* section of the tutorial. Different groups of instances are created along with their respective security groups and rules.

The database and message queue services are split into a separate instance called **instance_services**, a separate security group for this instance is also created.

Then, the API service is scaled into two different instances, which both run the API service. A different Floating IP address is assigned to each instance.

>These services are client-facing, so unlike the workers they do not use a message queue to distribute tasks. Instead, we must introduce some kind of load balancing mechanism to share incoming requests between the different API services.

>A simple solution is to give half of your friends one address and half the other, but that solution is not sustainable. Instead, we can use a DNS round robin to do that automatically. However, OpenStack networking can provide Load Balancing as a Service.

The workers are then scaled into 3 different worker instances. This allows dealing with a higher number of requests for fractals. As soon as these worker instances start, they begin checking the message queue for requests, reducing the overall backlog.
