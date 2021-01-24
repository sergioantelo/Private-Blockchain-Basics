First the blockchain nodes have to be started before starting the web app.
Start each node and the application in a separate terminal.

Starting blockchain nodes:
- python node_server.py <node_port> (the <> does not have to be written)

  Example: 2 Nodes for Blockchain network, listening on ports 8000 and 8001 respectively.
  NODE 1: python node_server.py 8000
  NODE 2: python node_server.py 8001

Starting website:
(After specifying the port where to host, you specify the ports of the nodes in the blockchain network. 
The first node address will be used to fetch the blockchain for visualizing. 
NOTE: When starting the webapp at least one node has to be specified, which will be the background node for the beginning.
Further blockchain nodes can then also be added through the web interface.) 

- python run_app.py <website_port> <sync_node_port> <further_node_port>... 

  Example: Starting Application, listening on port 5000. The nodes 8000 and 8001 are blockchain nodes.
  Application Server: python run_app.py 5000 8000 8001
  

after having started go to any browser and type:
localhost:<website_port>
-> this should show the web interface

to check if the blockchain nodes are running, they can be reached by:
localhost:<node_port>/chain
-> printing the blockchain instance (see code) in a raw format

(localhost == http://127.0.0.1:)