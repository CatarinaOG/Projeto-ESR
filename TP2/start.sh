#! /bin/bash

export DISPLAY=:0.0

if [ ${1} == "Server1" ]; then
    echo "Server1"
    python3 oNode.py server 10.0.3.10 config.json master
elif [ ${1} == "Server2" ]; then
    echo "Server2"
    python3 oNode.py server 10.0.7.10 config.json
elif [ ${1} == "Node1" ]; then
    echo "Node1"
    python3 oNode.py node 10.0.5.1 configNode.json
elif [ ${1} == "Node2" ]; then
    echo "Node2"
    python3 oNode.py node 10.0.3.1 configNode.json
elif [ ${1} == "Node3" ]; then
    echo "Node3"
    python3 oNode.py node 10.0.6.2 configNode.json
elif [ ${1} == "Node4" ]; then  
    echo "Node4"
    python3 oNode.py node 10.0.2.2 configNode.json
elif [ ${1} == "Client1" ]; then  
    echo "Client1"
    python3 oNode.py client 10.0.0.1
elif [ ${1} == "Client2" ]; then  
    echo "Client2"
    python3 oNode.py client 10.0.5.1
fi    
    
