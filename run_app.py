from flask import Flask,render_template, redirect, request
import requests
import datetime
import json
import sys
import time
from hashlib import sha256
import random

##########
#FELIX
######
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

@app.route('/search', methods=['POST'])
def search_textarea():
    """
    Endpoint to search for a transaction via our application.
    """
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)
    global answer
    if response.status_code == 200:
        content = request.form["content"]
        content = sha256(content.encode()).hexdigest()
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                if content == tx['hash']:
                    answer = "Transaction Found"
                    return redirect('/')
                else:
                    answer = "Transaction Not Found"
    
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

    print(CONNECTED_NODE_ADDRESS)

    app.run(debug=True,port=host_node)

