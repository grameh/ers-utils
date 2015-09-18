#!/usr/bin/python
import time
import subprocess
import uuid
import ast
import random
import json
import os

pipework_path = os.getcwd()+'/pipework'
interface = 'eth0'
docker_path = '/usr/bin/docker'
# In this test we simulate a truck going through a number of villages
# In each village there is a merchant which has a list of prices, stored on an ERS_CONTRIBUTOR
# The truck has an ERS bridge that will sync with each contributor.
# Contributors are interested in only some of the prices from other villages, and will get updated versions every time
# the truck passes by.

# at least 3
NR_INSTANCES = 4

def add_document_to_couchdb_in_docker(container_id, entity_id, dbname, statements):
    document_json = {"@id": entity_id}
    for key in statements.keys():
        document_json[key] = statements[key]


    command = "curl -s -X PUT localhost:5984/{db_name}/{docid} -d '{json_dump}'".format(db_name = dbname,\
                                                    docid = str(uuid.uuid4()).replace('-',''),
                                                    json_dump = json.dumps(document_json))

    os.system(docker_path + " exec {} {}".format(container_id, command))

def running_containers_list():
    running_containers_command = (docker_path + ' ps -q').split(' ')

    result = subprocess.check_output(running_containers_command)
    containers_list = []
    for container_id in result.split():
        containers_list.append(container_id)
    return containers_list

def link_nodes(container_list):
    #connect all contributors to a different subnet to simulate different villages
    #bridge will connect to each subnet in turn
    for i in range(len(container_list)):
        container_id = container_list[i]
        pipeworks_command = 'sudo ' + pipework_path + ' ' + interface + ' ' + container_id +' 192.168.' + str(i) + '.200/24'
        os.system(pipeworks_command)
        wait_command = 'sudo ' + pipework_path + ' --wait -i ' + interface
        os.system(wait_command)

def remove_pipeworks_interface(container_id, interface_nr):
    #remove pipeworks interface from container
    if container_id[-1] == '\n':
        container_id = container_id[:-1]
    command = 'ifconfig eth'+ str(interface_nr)  +' down'
    full_cmd = (docker_path + " exec {} {}").format(container_id, command)
    os.system(full_cmd)
    #host_cmd = 'sudo ifconfig hostbridge down'
    #os.system(host_cmd)

def add_bridge_pipework_interface(container_id, interface_nr):
    #connect bridge to one of the contributors
    #if container_id[-1] == '\n':
    #    container_id = container_id[:-1]
    #pipeworks_command = 'sudo ' + pipework_path + ' ' + interface + ' -i eth1 -l hstbr  ' + container_id + ' 192.168.' + str(subnet_id) + '.250/24'
    #os.system(pipeworks_command)
    #wait_command = 'sudo ' + pipework_path + ' --wait -i ' + interface
    #os.system(wait_command)

    #bring up interface
    if container_id[-1] == '\n':
        container_id = container_id[:-1]
    command = 'ifconfig eth'+ str(interface_nr)  +' up'
    full_cmd = (docker_path + " exec {} {}").format(container_id, command)
    os.system(full_cmd)

def populate_prices_contributors(container_list):
    vendor_items = 3
    for i in range(len(container_list)):
        # add initial prices
        container_id = container_list[i]
        node_id = chr(ord('A')+i)
        node_information = {'ers:Item' + node_id + '1': str(i),
                            'ers:Item' + node_id + '2': str(i),
                            'ers:type': 'ers:Vendor'}
        for j in range(vendor_items):
            node_information['ers:Item' + node_id + str(j)] = str(0)

        # test shouldn't really have more than 27 nodes
        add_document_to_couchdb_in_docker(container_id, node_id, 'ers-public', node_information)

def start_nodes():
    command = (docker_path + " run -d grameh/ers")

    for i in range(NR_INSTANCES):
        #result = subprocess.check_output(command.split())
        os.system(command)
        time.sleep(1)

def start_bridge():
    command = (docker_path + ' run --privileged -d grameh/ers-bridge')

    result = subprocess.check_output(command.split(' '))

    time.sleep(2)
    container_id = result
    if container_id[-1] == '\n':
        container_id = container_id[:-1]

    #create all the subnets
    for subnet_id in range(0, NR_INSTANCES):
        pipeworks_command = 'sudo ' + pipework_path + ' ' + interface + ' -i eth' + str(1 + subnet_id) + ' '  + container_id + ' 192.168.' + str(subnet_id) + '.250/24'
        os.system(pipeworks_command)
        wait_command = 'sudo ' + pipework_path + ' --wait -i ' + interface
        os.system(wait_command)

    # make them unavailable
    for interface_id in range(1, NR_INSTANCES + 1):
        command = 'ifconfig eth'+ str(interface_id)  +' down'
        full_cmd = (docker_path + " exec {} {}").format(container_id, command)
        os.system(full_cmd)

    return result

def remove_all_docker():
    kill_command = docker_path + ' exec {} pkill python'
    containers = running_containers_list()
    for container_id in containers:
        os.system(kill_command.format(container_id))

    all_containers_command = (docker_path + ' ps -a -q').split(' ')
    result = subprocess.check_output(all_containers_command)
    result = result.replace('\n', ' ')
    #os.system(docker_path + ' kill ' + result)
    os.system(docker_path + ' rm ' + result)

def main():
    start_nodes()
    time.sleep(2)
    #populate initial prices
    container_list = running_containers_list()
    node_id_list = [chr(ord('A') + i) for i in range(len(container_list))]
    populate_prices_contributors(container_list)
    # at this point, each contributor has his own price list
    # create a subnet for each of them
    link_nodes(container_list)

    #create bridge
    bridge_id = start_bridge()

    # each vendor is interested in the prices of his neighbors (e.g. b is interested in a and c)
    # so the first time the truck arrives, he performs a search for those entities and caches the documents.
    # after this initial step, prices will be updated automagically
    for i in range(NR_INSTANCES):
        print "in loop"
        #connect bridge to container 'container_list[i]'
        add_bridge_pipework_interface(bridge_id, i + 1)
        import pdb;pdb.set_trace()

        #search for neighbors
        if i == 0:
            left_peer = node_id_list[-1]
        else:
            left_peer = node_id_list[i-1]
        if i == NR_INSTANCES - 1:
            right_peer = node_id_list[0]
        else:
            right_peer = node_id_list[i+1]
        #search for other vendors
        command = 'curl -s localhost:5000/Search/ers:type/ers:Vendor'
        cache_command = 'curl -s localhost:5000/CacheEntity/'

        container_id = container_list[i]
        full_cmd = docker_path + " exec " + container_id + " " + command
        output = subprocess.check_output(full_cmd.split(' '))
        entities_list = ast.literal_eval(output)
        print "got entities"
        #cache left and right peer if they are available on the bridge
        try:
            entities_list.index(left_peer)
            full_cmd = docker_path + " exec " + container_id + " " + cache_command + left_peer
            output = subprocess.check_output(full_cmd.split(' '))
        except:
            # peer not found on brige, skip?
            pass

        try:
            entities_list.index(right_peer)
            full_cmd = docker_path + " exec " + container_id + " " + cache_command + right_peer
            output = subprocess.check_output(full_cmd.split(' '))
        except:
            # peer not found on brige, skip?
            pass

        import pdb;pdb.set_trace()
        #disconnect truck from peer
        remove_pipeworks_interface(bridge_id, i + 1)

    NR_STEPS_TEST = 10
    # truck starts moving around and getting updated versions
    for i in range(NR_STEPS_TEST):
        # connect to node i%NR_INSTANCES
        contributor = i % NR_INSTANCES
        # sync up
        add_bridge_pipework_interface(bridge_id, contributor)

        # wait
        time.sleep(1)

        # disconnect
        remove_pipeworks_interface(bridge_id)

    remove_all_docker()

if __name__ == "__main__":
    main()
