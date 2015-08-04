instances=`docker ps -q`
for i in $instances
    do
    docker exec $i pkill python
done
docker kill $(docker ps -a -q)
docker rm $(docker ps -a -q)
