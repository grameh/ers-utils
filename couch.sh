# for 14.04 release
sudo apt-get install software-properties-common -y
# add the ppa
sudo add-apt-repository ppa:couchdb/stable -y
# update cached list of packages
sudo apt-get update -y
# remove any existing couchdb binaries
sudo apt-get remove couchdb couchdb-bin couchdb-common -yf
# see my shiny goodness - note the version number displayed and ensure its what you expect
sudo apt-get install -V couchdb

# manage via upstart
sudo stop couchdb
# update /etc/couchdb/local.ini with 'bind_address=0.0.0.0' as needed
sudo start couchdb
