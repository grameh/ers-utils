#!/usr/bin/python
import re
import json
import threading
import time
import random
import uuid
import ast
from copy import deepcopy
import os
import subprocess
NR_INSTANCES=3
pipework_path = os.getcwd()+'/pipework'
interface = 'eth1'
docker_path = '/usr/bin/docker'
LANGUAGES_LIST = ['java', 'c', 'c++', 'matlab', 'r', 'go', 'rust', 'bash', 'c#', 'python', 'ruby',
                  'perl', 'php', 'html', 'css', 'javascript', 'sql', 'objective-c', 'swift']
#random list of companies where johndoes work
COMPANIES_LIST = ['google', 'facebook', 'microsoft', 'intel', 'ibm', 'oracle', 'sap', 'symatec', 'vmware',
                  'twitter', 'cisco', 'airbnb', 'uber', 'nvidia', 'apple', 'linkedin']

#global variable containing statement documents ids
doc_list = []

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


def start_nodes():
    command = (docker_path + " run -d grameh/ers:test")

    for i in range(NR_INSTANCES):
        #result = subprocess.check_output(command.split())
        os.system(command)

def link_nodes():
    container_list = running_containers_list()
    for i in range(len(container_list)):
        container_id = container_list[i]
        pipeworks_command = 'sudo ' + pipework_path + ' ' + interface + ' ' + container_id +\
                                ' 192.168.0.' + str(200 + i) +'/24'
        os.system(pipeworks_command)

def search():
    command = 'curl -s localhost:5000/Search/ers:type/ers:ConferenceAttendee'
    container_list = running_containers_list()
    for i in range(len(container_list)):
        container_id = container_list[i]
        full_cmd = docker_path + " exec " + container_id + " " + command
        output = subprocess.check_output(full_cmd.split(' '))
        print "node " + str(i) + " output"
        print output


def cache_entities():
    command = 'curl -s localhost:5000/Search/ers:type/ers:ConferenceAttendee'
    cache_command = 'curl -s localhost:5000/CacheEntity/'
    container_list = running_containers_list()
    for i in range(len(container_list)):
        container_id = container_list[i]
        full_cmd = docker_path + " exec " + container_id + " " + command
        output = subprocess.check_output(full_cmd.split(' '))
        entities_list = ast.literal_eval(output)
        for entity in entities_list:
            full_cmd = docker_path + " exec " + container_id + " " + cache_command + entity
            output = subprocess.check_output(full_cmd.split(' '))

def add_random_statements():
    # each node makes a random number of "endorsements" to other conference attendees
    max_nr_peers_endorsed = 10
    max_nr_endorsements = 10
    container_list = running_containers_list()
    if len(container_list) < 2:
        print "only one participant!"
        return
    all_statements = []
    global doc_list
    for participant in container_list:
        #he makes nr_endorsements to nodes other than himself
        for i in range(0, random.randint(1,max_nr_peers_endorsed)):
            # the list of peers
            # this is the list of documents in ers-cache flask/ShowDB/<db_name>

            #extract all doc ids
            command = 'curl -s localhost:5000/Search/ers:type/ers:ConferenceAttendee'
            full_cmd = docker_path + " exec " + participant + " " + command
            output = subprocess.check_output(full_cmd.split(' '))
            participant_list = ast.literal_eval(output)

            participant_name = random.choice(participant_list)
            # get the nodes's skills list
            # flask/ShowDBDocument/<db_name>/<entity_name>
            command = docker_path + ' exec ' + participant + ' curl -s localhost:5000/ShowDBDocument/ers-cache/' + participant_name
            result = subprocess.check_output(command.split(' '))
            result = json.loads(result)

            skill_list = result['ers:skills']
            skill_choice = random.choice(skill_list)

            # pick a skill and endorse it
            # flask/AddStatement/<entity>/<predicate>/<value>
            command = docker_path + ' exec ' + participant + ' curl -s localhost:5000/AddStatement/' + participant_name + '/ers:endorsement/' + skill_choice
            result = subprocess.check_output(command.split(' '))
            new_doc_id = result.split()[-2]
            doc_list.append(new_doc_id)
            print doc_list

def how_many_documents_in_cache():
    # check how many documents in doc_list are visible on each peer
    if len(doc_list) > 0:
        container_list = running_containers_list()
        list_cache_command = 'curl -s localhost:5984/ers-cache/_all_docs'
        for container in container_list:
            full_cmd = 'docker exec ' + container + ' ' + list_cache_command
            result = subprocess.check_output(full_cmd.split(' '))
            nr_found = 0
            for doc in doc_list:
                if doc in result:
                    nr_found += 1
            print 'On container {} found {} percent'.format(container, float(nr_found)/len(doc_list))

def poll_nodes():
    for i in range(0,10):
        how_many_documents_in_cache()
        time.sleep(1)


def main():
    # monitoring done in a separate process:
    # query all the nodes, see how many peers they see
    # and how many statements they see about themselves in their cache

    #first, start the nodes
    start_nodes()
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
    #get all entities, then cache them so that we trigger replication
    cache_entities()

    print "starting monitoring thread"
    t = threading.Thread(target = poll_nodes)
    t.start()

    #make random statements, see how fast it takes to see them
    add_random_statements()

    # each node must search for themselves and see whether others have made statements
    # about them
    #clear
    remove_all_docker()

if __name__ == "__main__":
    main()
