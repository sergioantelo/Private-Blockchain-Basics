from flask import Flask,render_template, redirect, request
import requests
import datetime
import json
import sys
import time
from hashlib import sha256
import random
import os

##########
#FELIX
#####
# Before package structre, with importing the app variable from the app folder, and calling app.run here, and having
# the application code (view) in separate file. Probably there was a reason, but so far it works this way too and is maybe more intuitive
###### 


app = Flask(__name__)
localhost = "http://127.0.0.1:"
NODE_ADDRESS_list = []
CONNECTED_NODE_ADDRESS = ""
posts = []
txs = []
answer = ""
answer_error = ""
difficulty = "2"
difficulty_error = ""
available_nodes = []
connected_node = localhost+'8000'
connected_node_error = ""
new_node = ""
del_node = ""
register = ""
register_error = ""
tamp_block = ""
attack = ""
  
pool_of_unmined_txs = []


def fetch_posts():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            #for tx in block["transactions"]:
                #tx["index"] = block["index"]
                #tx["hash"] = block["previous_hash"]
            content.append(block)

        global posts
        posts = sorted(content, key=lambda k: k['timestamp'],
                       reverse=True)

def fetch_pending_txs():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    global txs
    txs = pool_of_unmined_txs

@app.route('/')
def index():
    fetch_posts()
    fetch_pending_txs()
    return render_template('index.html',
                           title='LMU University: Decentralized Certificates Storage',
                           posts=posts,
                           txs=txs,
                           answer = answer,
                           answer_error = answer_error,
                           difficulty = difficulty,
                           difficulty_error = difficulty_error,
                           available_nodes = NODE_ADDRESS_list,
                           connected_node = connected_node,
                           connected_node_error = connected_node_error,
                           new_node = new_node,
                           del_node = del_node,
                           register = register,
                           register_error = register_error,
                           tamp_block = tamp_block,
                           attack = attack,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string)


@app.route('/submit', methods=['POST'])
def submit_textarea():
    """
    Endpoint to create a new transaction via our application.
    """
    post_content = request.form["content"]
    author = request.form["author"]
    # FELIX
    timestamp = time.time()
    
    tx_hash = sha256(post_content.encode()).hexdigest()

    transaction = {
        'author': author,
        'content': post_content,
        'timestamp': timestamp,
        'hash': tx_hash
    }

    pool_of_unmined_txs.append(transaction)

    return redirect('/')

@app.route('/mine_app')
def start_mining():
    """
    Endpoint to simulate mining in network.
    """
    select_rnd_node = random.choice(NODE_ADDRESS_list)

    address = "{}/new_transaction".format(select_rnd_node)
    global pool_of_unmined_txs
    for tx in pool_of_unmined_txs:
        requests.post(address,
                      json=tx,
                      headers={'Content-type': 'application/json'})
    
    address = "{}/mine".format(select_rnd_node)
    response = requests.get(address)

    if response.status_code == 200:
        pool_of_unmined_txs = []

    return response.text

@app.route('/search', methods=['POST'])
def search_textarea():
    """
    Endpoint to search for a transaction via our application.
    """
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    global answer
    global answer_error
    if response.status_code == 200:
        content = request.form["content"]
        try: 
            content = int(content)
            answer = ""
            answer_error = "Please input a valid content"
            return redirect('/')
        except:
            content = sha256(content.encode()).hexdigest()
            chain = json.loads(response.content)
            for block in chain["chain"]:
                for tx in block["transactions"]:
                    if content == tx['hash']:
                        answer = "Transaction Found"
                        answer_error = ""
                        return redirect('/')
                    else:
                        answer = "Transaction Not Found"
                        answer_error = ""
    
    return redirect('/')

@app.route('/switch_node', methods=['POST'])
def switch_connected_node():
    node = request.form["node"]
    node_address = localhost+node

    global CONNECTED_NODE_ADDRESS
    global connected_node
    global connected_node_error

    if node_address not in NODE_ADDRESS_list:
        print("Hello")
        connected_node = CONNECTED_NODE_ADDRESS
        connected_node_error = "Please input a valid node"
        return redirect('/')
    else:
        try: 
            node = int(node)
            for node in NODE_ADDRESS_list:
                if node_address == node:
                    CONNECTED_NODE_ADDRESS = node_address
                    connected_node = node_address
                    connected_node_error = ""
                    return redirect('/')
                else:
                    pass
            return redirect('/')
        except:
            connected_node = CONNECTED_NODE_ADDRESS
            connected_node_error = "Please input a valid node"
            return redirect('/')

@app.route('/add_new_node', methods=['POST'])
def add_node():
    node = request.form["new_node"]
    node_address = localhost+node

    global new_node
    if node_address in NODE_ADDRESS_list:
        new_node = "Node already in the network"
        return redirect('/')
    else:
        try: 
            node = int(node)
            NODE_ADDRESS_list.append(node_address)
            new_node = ""
            return redirect('/')
        except:
            new_node = "Please input a valid node"
            return redirect('/')

@app.route('/delete_node', methods=['POST'])
def delete_node():
    node = request.form["del_node"]
    node_address = localhost+node

    global del_node
    if node_address in NODE_ADDRESS_list:
        NODE_ADDRESS_list.remove(node_address)
        del_node = ""
        return redirect('/')
    else:
        try: 
            node = int(node)
            del_node = "Node not in the network"
            return redirect('/')
        except:
            del_node = "Please input a valid node"
            return redirect('/')

@app.route('/modify_diff', methods=['POST'])
def modify_textarea():
    """
    Endpoint to change the difficulty via our application.
    """
    diff = request.form["difficulty"]

    for peer in NODE_ADDRESS_list:
        modify_address = "{}/modify_difficulty".format(peer)

        post_content = {"difficulty":diff}
        response = requests.post(modify_address,
                                 json=post_content,
                                 headers={'Content-type': 'application/json'})

    global difficulty
    global difficulty_error
    try: 
        diff = int(diff)
        difficulty = response.text
        difficulty_error = ""
        return redirect('/')
    except:
        difficulty_error = "Please input a valid difficulty"
        return redirect('/')
    
@app.route('/reg_with', methods=['POST'])
def reg_with():
    node_base = request.form["node1"]
    node_base_address = localhost+node_base

    list_nodes = request.form["list_nodes"]
    list_nodes_address = localhost+list_nodes
    global register
    global register_error

    # if no nodes to register with were submitted then the command is used to
    # synchronize the specified node_base with its peers, which is looking for the longest chain
    if not list_nodes:
        address = "{}/synchronize_with_peers".format(node_base_address)
        response = requests.get(address)
        register = ""
        register_error = response.text
        return redirect('/')

    elif node_base_address not in NODE_ADDRESS_list:
        register = ""
        register_error = "Please input an available node"
        return redirect('/')

    elif node_base_address == list_nodes_address:
        register = ""
        register_error = "Please don't register a node with itself"
        return redirect('/')

    elif (node_base_address in NODE_ADDRESS_list) and (list_nodes_address in NODE_ADDRESS_list):
        new_nodes = []
        new_nodes.append(list_nodes_address)
        post_content = {"peers_list":new_nodes}
        get_register_address = "{}/register_with".format(node_base_address)

        response = requests.post(get_register_address,
                        json=post_content,
                        headers={'Content-type': 'application/json'})

        register = response.text
        register_error = ""
        return redirect('/')


    list_nodes = list_nodes.replace(" ","")
    modified_list = list_nodes.split(",")
    new_nodes = []
    for node in modified_list:
        node = localhost+node
        new_nodes.append(node)

    if not all(elem in NODE_ADDRESS_list for elem in new_nodes):
        print(modified_list, NODE_ADDRESS_list, all(elem in NODE_ADDRESS_list for elem in modified_list))
        register = ""
        register_error = "Please input available nodes"
        return redirect('/')
    else:
        try: 
            node_base = int(node_base)
            for n in modified_list:
                n = int(n)
                
            post_content = {"peers_list":new_nodes}

            get_register_address = "{}/register_with".format(node_base_address)

            response = requests.post(get_register_address,
                            json=post_content,
                            headers={'Content-type': 'application/json'})

            register = response.text
            register_error = ""
            return redirect('/')
        except:
            register = ""
            register_error = "Please input a available nodes"
            return redirect('/')

@app.route('/tampered_block', methods=['POST'])
def tampered_block():
    address = "{}/attack".format(CONNECTED_NODE_ADDRESS)

    # has to be fetched from the specified check boxes
    attack_type = request.form["attack_type"]
    attack_type_dict = {"attack":attack_type}

    response = requests.post(address,
                            json=attack_type_dict,
                            headers={'Content-type': 'application/json'})
    
    response = json.loads(response.content)

    global attack
    global tamp_block
    if not response.get("block"):
        attack = response["message"]
        tamp_block = ""
        return redirect("/")

    tamp_block = response["block"]
    attack = response["message"]

    return redirect("/")

@app.route('/show_tampered_block')
def show_tampered_block():
    
    global tamp_block
    print(tamp_block)
    return tamp_block

def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')

##########
# FELIX
##########
if __name__=="__main__":
    host_node = sys.argv[1]
    
    blockchain_nodes = sys.argv[2:]
    for node in blockchain_nodes:
        NODE_ADDRESS_list.append(localhost+node)

    CONNECTED_NODE_ADDRESS = NODE_ADDRESS_list[0]

    app.run(debug=True,port=host_node)

