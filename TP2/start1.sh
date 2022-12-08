#! /bin/bash

export DISPLAY=:0.0

if [ ${1} == "Server1" ]; then
    echo "Server1"
    python3 oNode.py server 10.0.2.10 config1.json master
elif [ ${1} == "Node1" ]; then
    echo "Node1"
    python3 oNode.py node 10.0.1.1 configNode1.json
elif [ ${1} == "Node2" ]; then
    echo "Node2"
    python3 oNode.py node 10.0.2.1 configNode1.json
elif [ ${1} == "Client1" ]; then  
    echo "Client1"
    python3 oNode.py client 10.0.0.20 10.0.1.1
fi    
    
