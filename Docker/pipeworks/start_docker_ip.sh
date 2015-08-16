#!/bin/bash
#eth0 - the "real" interface to listen to
#last parameter is the ip
nr_instances=1

for (( i = 0 ; i < $nr_instances ; i++ ))
do
   #this might fail. retry
   myres=`docker run -d grameh/ers`
   #it might fail to start.. check against docker ps -q
   sudo ./pipework eth1 $myres 192.168.1.$((200 + $i))/24
   sleep 2
done
