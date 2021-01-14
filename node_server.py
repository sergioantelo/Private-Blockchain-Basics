from hashlib import sha256
import json
import time

import sys
from flask import Flask, request, redirect
import requests

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0, miner=""):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash

        self.nonce = nonce
        self.miner = miner

    def compute_hash(self):
        """
        A function that return the hash of the block contents.
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    # difficulty of our PoW algorithm
    difficulty = 2

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []

    def set_difficulty(self,diff):
        Blockchain.difficulty = diff

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block(0, [], 0, "0")
        # hash field has to be added after its creation !
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block
          in the chain match.
        """
        previous_hash = self.last_block.hash
        
        if previous_hash == proof:
            return (False,"Block already added")

        if previous_hash != block.previous_hash:
            return (False, "Previous hash not correct")

        block_validity = Blockchain.is_valid_proof(block,proof)
        '''
        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
 
        self.chain.append(block)
        '''
        if block_validity[0]:
            block.hash = proof
            self.chain.append(block)

        return block_validity

    @staticmethod
    def proof_of_work(block):
        """
        Function that tries different values of nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    def get_last_tx_timestamp(self):
        self.unconfirmed_transactions[-1]["timestamp"]


    @classmethod
    def is_valid_proof(cls, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """

        if not block_hash == block.compute_hash():
            return (False, "Hash not correct")

        if not block_hash.startswith('0' * Blockchain.difficulty):
            return (False, "Required difficulty not fullfilled")
        
        return (True, "Proof correct")
        #return (block_hash.startswith('0' * Blockchain.difficulty) and
        #        block_hash == block.compute_hash())

    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
            # remove the hash field to recompute the hash again
            # using `compute_hash` method.
            delattr(block, "hash")

            # [0] because the is_valid_proof returns a tuple
            if not cls.is_valid_proof(block, block_hash)[0] or previous_hash != block.previous_hash:
                result = False
                break

            block.hash, previous_hash = block_hash, block_hash

        return result

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash,
                          miner = request.host_url)

        proof = self.proof_of_work(new_block)

        self.add_block(new_block, proof)

        self.unconfirmed_transactions = []

        return True


app = Flask(__name__)
localhost = "http://127.0.0.1:"
# the node's copy of blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()

# the address to other participating members of the network
peers = set()

# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["author", "content", "timestamp"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404
    '''
    time_tx = tx_data["timestamp"]
    time_last_added_tx = blockchain.get_last_tx_timestamp()

    if(time_tx==time_last_added_tx):
        return "Transaction already received"
    else:

        blockchain.add_new_transaction(tx_data)

        for peer in peers:
            new_tx_address = "{}/new_transaction".format(peer)

            requests.post(new_tx_address,
                          json=json.dumps(tx_data),
                          headers={'Content-type': 'application/json'})
             
        return "Success", 201
    '''
    #tx_data["timestamp"] = time.time()

    blockchain.add_new_transaction(tx_data)

    return "Success", 201


# endpoint to return the node's copy of the chain.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data,
                       "peers": list(peers)})


# endpoint to request the node to mine the unconfirmed
# transactions (if any). We'll be using it to initiate
# a command to mine from our application itself.
@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():

    '''
    # checking if we already received mined transaction
    request_info = request.get_json()

    if not request_info.get("reached_nodes"):
        #return "Error", 201
        reached_nodes = []
    else:    
        node_address = request.host_url()
        reached_nodes = request_info["reached_nodes"]

    if node_address in reached_nodes:
        return "already received task"
    
    for peer in peers:
        new_peer_address = "{}/mine".format(peer)
        reached_nodes.append(node_address)

        requests.post(new_peer_address,
                      json=json.dumps(reached_nodes),
                      headers={'Content-type': 'application/json'})
    '''

    #wait() proportional to reached_nodes list, which will grow with a high steep and then saturated 
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    else:
        '''
        # Making sure we have the longest chain before announcing to the network
        chain_length = len(blockchain.chain)
               
        consensus()
        
        if chain_length == len(blockchain.chain):
            # announce the recently mined block to the network
            announce_new_block(blockchain.last_block)
        '''
        if peers:
            announce_new_block(blockchain.last_block)

        return "Block #{} is mined.".format(blockchain.last_block.index)


# endpoint to add new peers to the network.
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    ########
    #FELIX
    ########
    #chain = get_chain()
 
    # Add the node to the peer list
    peers.add(node_address)

    # Return the consensus blockchain to the newly registered node
    # so that he can sync
    #return chain

    return "New node added", 200

#D:\Felix\Documents\Studiumunterlagen\Vorlesungsskripte\Master_LMU\WS 20_21\DataSecurity&Ethics\Blockchain\python_blockchain_app
@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    """
    Internally calls the `register_node` endpoint to
    register current node with the node specified in the
    request, and sync the blockchain as well as peer data.
    """
    peers_list = request.get_json()["peers_list"]
    
    if not peers_list:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    '''
    # Make a request to register with remote node and obtain information
    response = requests.post(node_address + "/register_node",
                             data=json.dumps(data), headers=headers)
    '''

    for peer in peers_list:
        if peer in peers:
            continue
        print(peer)
        response = requests.post(peer + "/register_node",
                                 data=json.dumps(data), headers=headers)
        if response.status_code==200:
            print("peer was added")
            peers.add(peer)


    update_local_chain = consensus()
    
    '''       
    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and the peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        # peers.update(response.json()['peers'])
        ############
        #FELIX
        ############
        peers.add(node_address)
        
        
        return "Registration successful"+" "+node_address, 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code
    '''

    # update_local_chain[0] indicates whether the local chain was updated or not
    # if not it means no longer chain was found
    # update_local_chain[1] contains a list witht the peers whose chain was not valid
    
    if update_local_chain[0]:
        return "Registration successful. Chain updated", 200
    else:        
        return "Registration succesful. No longer chain found among peers"
        
# endpoint to add a block mined by someone else to
# the node's chain. The block is first verified by the node
# and then added to the chain.
@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"],
                  block_data["miner"])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)
    # added[0] whether block was added
    # added[1] message

    if added[1] == "Block already added":
        return json.dumps({"status":added[0],"message":added[1]})

   #if not added:
   #     return "The block was discarded by the node", 400

    # this node received a new block from one of its peers, and after the previous checks
    # this node will announce the new block also to its peers
    # thus the node is propagated through the network
    
    if added[0] and peers:
        announce_new_block(block)

    #return "Block added to the chain", 201

    return json.dumps({"status":added[0],"message":added[1]})

# endpoint to query unconfirmed transactions
@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)

@app.route('/add_default_block')
def add_fixed_block():
    global blockchain

    transaction = {
        'author': 'Peter Pan',
        'content': 'Wonderland',
        'timestamp': time.time(),
        'hash': sha256('Wonderland'.encode()).hexdigest()
    }
    last_block = blockchain.last_block
    default_block = Block(index=last_block.index + 1,
                           transactions=[transaction],
                           timestamp=time.time(),
                           previous_hash=last_block.hash,
                           miner=request.host_url)
    
    hash_default_block = Blockchain.proof_of_work(default_block)
    default_block.hash = hash_default_block
   
    blockchain.chain.append(default_block)

    return redirect("/chain")

@app.route('/attack')
def attack():
    '''
    Create a tampered block
    '''

    # attack where the transaction and the block fields are correct
    # but the attacker used a different last.block as reference
    # thus he is kind of "suggesting" an alternative blockchain 
    transaction = {
        'author': 'Sergio',
        'content': 'Attack',
        'timestamp': time.time(),
        'hash': sha256('Attack'.encode()).hexdigest()
    }

    #last_block = self.last_block
    tampered_block = Block(index=999,#last_block.index + 1,
                           transactions=[transaction],
                           timestamp=time.time(),
                           previous_hash='0x123abc',#last_block.hash,
                           miner=request.host_url)

    hash_tampered_block = Blockchain.proof_of_work(tampered_block)
    tampered_block.hash = hash_tampered_block

    #------------------------------------
    '''
    # ALTERNATIVE, no correct hash field due to later changes on transaction content
    transaction = {
        'author': 'Sergio',
        'content': 'I like icecream',
        'timestamp': time.time(),
        'hash': sha256('Attack'.encode()).hexdigest()
    }
    #global blockchain
    last_block = blockchain.last_block
    tampered_block = Block(index=last_block.index + 1,
                           transactions=[transaction],
                           timestamp=time.time(),
                           previous_hash=last_block.hash,
                           miner=request.host_url)
    
    hash_tampered_block = Blockchain.proof_of_work(tampered_block)
    tampered_block.hash = hash_tampered_block
    # no the block becomes tampered
    # because if you compute now the hash again, then it will not match with the hash field
    # but recomputing takes to much time for the attacker due to the "difficulty"
    
    #print("UDO:"+tampered_block.transactions[0]["content"])
    tampered_block.transactions[0]["content"] = "I hate icecream"
    '''
    if not peers:
        return "No peers existing"

    response = announce_new_block(tampered_block)

    if not response["status"]:
        # means that the block was not added
        return "Tampered block was identified: "+response["message"]
    else:
        # because we actively sent a uncorrect block, but if this was accepted then something
        # of the proofing alogorithms is not working
        return "Security mechanism is not working"

@app.route('/modify_difficulty')
def modify_difficulty(self,diff):
    '''
    Set a different difficulty
    '''
    blockchain.set_difficulty(diff)

def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue  # skip genesis block
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"],
                      block_data["miner"])
        proof = block_data['hash']
        added = generated_blockchain.add_block(block, proof)
        if not added[0]:
            # added[0] if the added block was added or not
            # added[1] what was the error
            return (added[0],added[1], block.index)
    return (True, generated_blockchain)

def consensus():
    """
    Our naive consnsus algorithm. If a longer valid chain is
    found, our chain is replaced with it.
    """
    global blockchain
    global peers

    longest_chain = None
    current_len = len(blockchain.chain)
    peers_list_with_incorrect_chains = []

    for peer in peers:
        response = requests.get('{}/chain'.format(peer))
        length = response.json()['length']
        chain = response.json()['chain']

        print("Length:",length)
        print("Current Length:", current_len)
        fetched_chain_feedback = create_chain_from_dump(chain)

        if not fetched_chain_feedback[0]:
            # then in this case fetched_chain_feedback[1] would be a message explaining
            # the error of the tampered block and fetched_chain_feedback[2] would be the index of the 
            # respective block
            peers_list_with_incorrect_chains.append((peer,fetched_chain_feedback[1], fetched_chain_feedback[2]))
            continue
        '''
        if length > current_len and blockchain.check_chain_validity(chain.chain):
            current_len = length
            longest_chain = chain
        '''
        peers_chain = fetched_chain_feedback[1]
        # peers_chain is an instance of Blockchain, peers_chain.chain is the attribute containing the 
        # the list of blocks, MAYBE CREATE an attribute like length for the Blockchain class 
        if len(peers_chain.chain) > current_len:
            current_len = length
            longest_chain = peers_chain

    if longest_chain:
        blockchain = longest_chain
        return (True, peers_list_with_incorrect_chains)

    return (False, peers_list_with_incorrect_chains)

def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    Other nodes can simply verify the proof of work and add it to their
    respective chains.
    """
    # gathering responses from its peers
    # responses of peer of peers are not propagated through
    responses = []
   
    for peer in peers:
        url = "{}/add_block".format(peer)
        headers = {'Content-Type': "application/json"}
        response = requests.post(url,
                                 data=json.dumps(block.__dict__, sort_keys=True),
                                 headers=headers)
        print(response.json())
        # response is a dictionary/json object, with the field status and message
        # status indicating if the block was added by the peer, message why potentially not
        responses.append(response.json())

    for r in responses:
        # the announced block was not added by this peer represented by r
        if not r["status"]:
            return r
    
    print(responses)
    return responses[0]


# Uncomment this line if you want to specify the port number in the code
#app.run(debug=True, port=8000)

if __name__=="__main__":
    port = sys.argv[1]
    app.run(debug=True,port=port)
    
    