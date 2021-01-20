Starting blockchain nodes:
- python node_server.py <node_port> (the <> does not have to be written)

Starting website:
- python run_app.py <website_port> <sync_node_port> <further_node_port>... (after specifying the port where to host, you specify the ports
                                                                             of the nodes in the blockchain network. The first node address
                                                                             will be used to fetch the blockchain for visualizing.)