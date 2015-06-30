#installation:
install vagrant
install virtualbox

clone ers-node
clone ers-utils

add ubuntu box: `vagrant box add ubuntu/trusty64`

first creation of vms : `vagrant up` (from the directory with the Vagrant file: ers-utils)

- **(optional)**: get a coffee, it will take a while

going on machines: `Vagrant ssh <machine_name>`

unit tests: `python unit_tests.py` (in ers-node directoryirectory. by default

this will be /vagrant/ers-node in the virtual machines)

stress tests: `python stress_tests.py`

for replication the replication tests have ip addresses hardcoded. Theexperimental setup is:

make sure node1 and node2 are running (`vagrant status` in ers-utils directory or `vagrant global-status` from anywhere on the main machine)

`vagrant ssh node1` (in directoryirectoryory with vagrant file)

- make sure the daemon is running (ps aux | grep “ers” should display the daemon process running. If not, just run `python ers/daemon.py --config /etc/ers-node/ers-node.ini` from the /vagrant/ers-node directory)

`python web_api.py` (start web api from /vagrant/ers-node1e in the VM)

repeat previous 3 commands for node2

shh into node13 and run replication_test from /vagrant/ers-node)
