FROM ubuntu:14.04
RUN apt-get update ; apt-get install -y git \
                                        vim \
                                        curl \
                                        wget \
                                        tar \
                                        python-dev \
                                        python-pip \
                                        python-couchdb

RUN pip install --upgrade http-parser \
                          socketpool \
                          restkit \
                          virtualenv \
                          rdflib \
                          CouchDB \
                          flask \
                          futures \
                          requests \
                          mock

#base image up to here
#now avahi
RUN apt-get install -y avahi-dbg \
                       avahi-dnsconfd \
                       avahi-utils \
                       avahi-daemon \
                       avahi-discover \
                       avahi-autoipd \
                       avahi-ui-utils


VOLUME ["/var/run/couchdb", "/var/run/dbus"]
RUN apt-get install software-properties-common -y
RUN add-apt-repository ppa:couchdb/stable -y
RUN apt-get install couchdb -y

ADD couchdb_default.ini /etc/couchdb/local.ini

#clone ers
RUN git clone https://github.com/grameh/ers-node.git /home
ADD ers-config.ini /etc/ers-node/ers-node.ini

#start stuff
ADD start_daemons.sh /tmp/start_daemons.sh

#RUN couchdb -b
EXPOSE 5984
EXPOSE 5678
EXPOSE 80
CMD sh /tmp/start_daemons.sh
