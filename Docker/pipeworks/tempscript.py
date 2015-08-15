#!/usr/bin/python
import json
import time
import random
from copy import deepcopy
import os
import subprocess
NR_INSTANCES=2
pipework_path = '/home/mga/Documents/thesis/ers-utils/Docker/pipeworks/pipework'
docker_path = '/usr/bin/docker'
LANGUAGES_LIST = ['java', 'c', 'c++', 'matlab', 'r', 'go', 'rust', 'bash', 'c#', 'python', 'ruby',
                  'perl', 'php', 'html', 'css', 'javascript', 'sql', 'objective-c', 'swift']
#random list of companies where johndoes work
COMPANIES_LIST = ['google', 'facebook', 'microsoft', 'intel', 'ibm', 'oracle', 'sap', 'symatec', 'vmware',
                  'twitter', 'cisco', 'airbnb', 'uber', 'nvidia', 'apple', 'linkedin']

def add_document_to_couchdb_in_docker(container_id, entity_id, dbname, statements):
    document_json = {"@id": entity_id}
    for key in statements.keys():
        document_json[key] = statements[key]


    command = "curl -X PUT localhost:5984/{db_name}/{docid} -d '{json_dump}'".format(db_name = dbname,\
                                                    docid = entity_id,
                                                    json_dump = json.dumps(document_json))

    os.system(docker_path + " exec {} {}".format(container_id, command))


def running_containers_list():
    running_containers_command = (docker_path + ' ps -q').split(' ')

    result = subprocess.check_output(running_containers_command)
    containers_list = []
    for container_id in result.split():
        containers_list.append(container_id)
    return containers_list

def remove_all_docker():
    kill_command = docker_path + ' exec {} pkill python'
    containers = running_containers_list()
    for container_id in containers:
        os.system(kill_command.format(container_id))

    all_containers_command = (docker_path + ' ps -a -q').split(' ')
    result = subprocess.check_output(all_containers_command)
    result = result.replace('\n', ' ')
    os.system(docker_path + ' kill ' + result)
    os.system(docker_path + ' rm ' + result)


def start_nodes():
    command = (docker_path + " run -d grameh/ers").split(' ')

    for i in range(NR_INSTANCES):
        result = subprocess.check_output(command)

def link_nodes():
    container_list = running_containers_list()
    for i in range(len(container_list)):
        container_id = container_list[i]
        pipeworks_command = 'sudo ' + pipework_path + ' eth0 ' + container_id +\
                                ' 192.168.0.' + str(200 + i) +'/24'
        os.system(pipeworks_command)

def search():
    command = 'curl localhost:5000/Search/ers:type/ers:ConferenceAttendee'
    container_list = running_containers_list()
    for i in range(len(container_list)):
        container_id = container_list[i]
        full_cmd = docker_path + " exec " + container_id + " " + command
        output = subprocess.check_output(full_cmd.split(' '))
        print "node " + str(i) + "i output"
        print output

    pass

def main():
    #first, start the nodes
    start_nodes()
    time.sleep(2)
    #then, add "offline" statements to them, describing their profile
    container_list = running_containers_list()
    for i in range(len(container_list)):
        # build up a node's "profile"
        container_id = container_list[i]
        node_information = {'ers:skills':[],\
                            'ers:type': 'ers:ConferenceAttendee',
                            'ers:work_place': random.choice(COMPANIES_LIST)}
        temp_skills = deepcopy(LANGUAGES_LIST)
        nr_skills = random.randint(1,len(temp_skills))
        for _ in range(nr_skills):
            # ugly code but written fast -_-'
            skill = random.choice(temp_skills)
            node_information['ers:skills'].append(skill)
            del temp_skills[temp_skills.index(skill)]

        add_document_to_couchdb_in_docker(container_id, 'JohnDoe'+str(i), 'ers-public', node_information)

    #connect nodes(bring them online)
    link_nodes()
    #query for people in the conference, see how fast can view all profiles
    search()

    #make random statements, see how fast it takes to see them
    #clear
    remove_all_docker()

if __name__ == "__main__":
    main()
