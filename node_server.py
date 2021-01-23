from flask import Flask, request, redirect, render_template
import requests
import numpy as np 
import json
import time
from hashlib import sha256
import sys

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
        For the block (self) the function computes the hash using the sha256 algorithm.
        The calculated hash is returned. For computing the hash the block object is transformed into a string
        by using the .__dict__ attribute of a python object and json.dumps. Thus the hash calculation depends
        on all fields and contents of the block attribute.
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

class Blockchain:

    def __init__(self):
        '''
        - list of transactions which will be taken to calculate the next block
        - chain: list of blocks
        - difficulty: specifying the number of leading zeros a hash has to have to be a valid proof
        '''
        self.pending_transactions = []
        self.chain = []
        self.difficulty = 2
        
    def add_genesis_block(self):
        """
        This function creates a default block used to create the first block in the blockchain.
        The block has no content  and no previous hash.
        """
        genesis_block = Block(0, [], 0, "0")
        
        # hash field has to be added after its creation !
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)
   
    def add_new_transaction(self, transaction):
        '''
        Adds a new transaction to the list of transactions which will become the next block
        '''
        self.pending_transactions.append(transaction)

    def set_difficulty(self,diff):
        '''
        Method to change the difficulty.
        '''
        if(diff<=0):
            return False
        
        self.difficulty = diff
        return True
    
    '''
    @property
    def get_difficulty(self):
         
        #Methods to return the difficulty
         
        return self.difficulty
    '''
    @property
    def get_last_block(self):
        '''
        Returns the last block in the chain list.
        '''
        return self.chain[-1]

    def retrieve_block(self, idx):
        '''
        Returns the block with the specified index from the blockchain.
        '''
        if idx < 0 or idx > len(self.chain):
            return False

        for b in self.chain:
            if idx == b.index:
                return b
        
        # NO block with specified index present
        return False

    def add_block(self, block, proof):
        """
        Receives a block object and a proof, which is a hash. The function checks, whether all
        of the block properties are valid: previous_hash equals hash of last block and if the provided hash
        is indeed the correct given the blocks content and has the necessary difficulty.
        """

        previous_hash = self.get_last_block.hash        
      
        if previous_hash == proof:
            # since each node sends a new block to its peers
            # a node receives each block it sent from its peers back, thus 
            # it checks whether it already has this block as last block
            return (False,"Block already added")

        if previous_hash != block.previous_hash:
            return (False, "Previous hash not correct")

        
        if not proof == block.compute_hash():
            return (False, "Hash not correct")

        if not proof.startswith('0' * self.difficulty):
            return (False, "Required difficulty not fullfilled")
        
        block.hash = proof
        self.chain.append(block)

        return (True, "Proof correct")
      
    def mine(self):
        """
        This function is the center function for mining a new block. It creates a new Block object
        by taking all transactions in the pending_transactions list. Then it creates a proof for this block,
        i.e. calculating a hash with the desired property by altering the nonce field. Finally it will add the 
        hash field to the block add the block to the blockchain and empties the list of unconfirmed transactions.
        """
        if not self.pending_transactions:
            return False

        last_block = self.get_last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.pending_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash,
                          miner = request.host_url)

        proof = self.proof_of_work(new_block)

        #self.add_block(new_block, proof)
        new_block.hash = proof
        self.chain.append(new_block)

        self.pending_transactions = []

        return True

    def proof_of_work(self,block):
        """
        This function finds a "proof" for a provided block. It is altering the nonce field and computing the hash
        for the resulting block. If the hash has the desired property this hash is returned. The nonce is changed inplace
        in the block object.
        """
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    '''
    def check_block_hash_correctness(self, block, block_hash):
        """
        This function takes a block and a hash and tests whether this hash is a valid proof. This means
        the hash should be the computed hash for the given block and start with the reuired number of 0s.
        This function is needed when a node receives a block from one of its peers.

        The function returns a tuple: first field: whether hash is correct, second field: why not, in case.
        """

        if not block_hash == block.compute_hash():
            return (False, "Hash not correct")

        if not block_hash.startswith('0' * self.difficulty):
            return (False, "Required difficulty not fullfilled")
        
        return (True, "Proof correct")
    '''

    """
    def check_chain_validity(self, chain):
        '''
        Method which checks whether a whole chain (list of blocks) is valid, for each block:
        - contained hash field matches hash re calculation ?
        - hash fulfills difficulty
        - previous hashes are correct

        For checking the hash validity it uses the check_block_hash_correctness function.
        '''
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
            # !!! remove the hash field to recompute the hash again !!!
            # using `compute_hash` method.
            delattr(block, "hash")

            # [0] because the check_block_hash_correctness returns a tuple
            if not self.check_block_hash_correctness(block, block_hash)[0] or previous_hash != block.previous_hash:
                result = False
                break
            
            # add hash field back to block object and adapt previous_hash
            block.hash, previous_hash = block_hash, block_hash

        return result
        """

# start FLASK enviornment
app = Flask(__name__)

# the node's copy of blockchain
blockchain = Blockchain()
blockchain.add_genesis_block()
# set of addresses of nodes in the network: set of peers
peers = set()

'''
The following functions are necessary for the network communication. These functions can be triggerd
via HTTP requests and receive and/or return data. These functions are necessary to exchange data
between the peers and the application server.
'''

@app.route('/add_transaction', methods=['POST'])
def new_transaction():
    '''
    Enterpoint to tell the node to add a new transactions. This transaction will be overtaken into the 
    list of pending transactions of the blockchain instance.
    '''

    tx_data = request.get_json()
    # the following keys are required to be contained in the transmitted data
    mandatory_keys = ["author", "content", "timestamp"]

    for key in mandatory_keys:
        if not tx_data.get(key):
            return "Invalid data", 400
   
    global blockchain
    blockchain.add_new_transaction(tx_data)

    return "Success", 201

@app.route('/mine', methods=['GET'])
def mine_pending_transactions():
    '''
    Request the node to create a new block using the list of transactions in the blockchain object. If this node
    has some peers, it will propagate its mined block to these nodes. Function returns a notification.
    '''
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    else:
        if peers:
            submit_block_to_network(blockchain.get_last_block)

        return "Block #{} is mined.".format(blockchain.get_last_block.index)

def submit_block_to_network(block):
    """
    If a node has mined a new block or it has received a correct block from one of its peers, the node will submit
    this block to its peers. This way a new block gets propagated through the network.

    The function returns a dictionary with the field status and message. Status explaining whether the block 
    was added by the peers and a message why potentially not.
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

@app.route('/add_block', methods=['POST'])
def check_and_add_received_block():
    '''
    This function is called by one of this nodes peers. The node receives a new mined block. The node 
    check if this block is valid. If the block is a correct successor of its blockchain it will add the block
    and announce the block to its peers.
    '''
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

    # this node received a new block from one of its peers, and after the previous checks
    # this node will announce the new block also to its peers
    # thus the node is propagated through the network
    
    # only if peers are known the announce is called, and when the received block is correct 
    if added[0] and peers:
        submit_block_to_network(block)
       
    return json.dumps({"status":added[0],"message":added[1]})

@app.route('/add_default_block')
def add_default_block():
    '''
    Function which adds to the blockchain a new default block. This block will also not be propagated to the nodes
    peers. The function might be used for test purposes, e.g. to actively create inconsistency between the nodes
    blockchains.
    '''
    global blockchain

    transaction = {
        'author': 'Peter Pan',
        'content': 'Wonderland',
        'timestamp': time.time(),
        'hash': sha256('Wonderland'.encode()).hexdigest()
    }
    last_block = blockchain.get_last_block
    default_block = Block(index=last_block.index + 1,
                           transactions=[transaction],
                           timestamp=time.time(),
                           previous_hash=last_block.hash,
                           miner=request.host_url)
    
    hash_default_block = blockchain.proof_of_work(default_block)
    default_block.hash = hash_default_block
   
    blockchain.chain.append(default_block)

    return redirect("/chain")

@app.route('/register_with', methods=['POST'])
def register_and_synch_with_existing_nodes(): 
    """
    This function will be used to build the network connectivity. The function's POST data is a list of
    addresses of nodes in the network. The node for which this function is called will add these peers
    to its peers set. Then it makes itself known to these nodes by triggering the add_new_peer function for
    these nodes.
    After having registered itself to the newly received peers, the node calls the consensus function and
    retrieves the chains from ALL its peers and stores the longest chain found as its version.

    This function will be used when a new node should be added to an existing network of nodes. However it can 
    also be used to register new peers to an exisitng node.
    """
    peers_list = request.get_json()["peers_list"]
    
    if not peers_list:
        return "Invalid data", 400

    # some peers were submitted, thus it will be checked if these peers are known to this node
    # if not the node will register itself to the specified peers
    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    for peer in peers_list:
        if peer in peers:
            continue
        response = requests.post(peer + "/register_node",
                                 data=json.dumps(data), headers=headers)
        if response.status_code==200:
            peers.add(peer)

    # ask all of its known peers for their blockchain and takes over
    # the longst chain found unless its chain has equal or greater length
    update_local_chain = consensus()
   
    # update_local_chain[0] indicates whether the local chain was updated or not
    # if not it means no longer chain was found
    # update_local_chain[1] contains a list witht the peers whose chain was not valid    
    if update_local_chain[0]:
        return "Registration successful. Chain updated", 200
    else:        
        return "Registration succesful. No longer chain found among peers"

@app.route('/register_node', methods=['POST'])
def add_new_peer_to_set():
    '''
    Tell a node to add a transmitted node address into its set of peers. This function
    will be called from another node which is new to a network and wants to let the other nodes know
    that it exists.
    '''
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400
 
    # Add the node to the peer list
    peers.add(node_address)

    return "New node added", 200

@app.route('/synchronize_with_peers')
def synch_with_peers():
    '''
    Function which triggers a synchronization. This node is asking for all blockchains of its peers. It it 
    finds a chain longer than its own, it will overtake this one.
    '''
    synch = consensus()

    if not peers:
        return "No peers to synchronize with."

    if synch[0]:
        return "Synchronisation succesful."
    else:
        return "No longer chain found among peers."

@app.route('/pending_tx')
def get_pending_tx():
    '''
    Returns all transactions which are in the current list of pending transaction.
    '''
    return json.dumps(blockchain.pending_transactions)

@app.route('/chain', methods=['GET'])
def get_chain():
    '''
    Function to return the whole blockchain version of a node.
    Will be needed when a new node is registered to the network and for the application to print the 
    blockchain.
    '''

    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)

    return json.dumps({"length": len(chain_data),
                       "chain": chain_data,
                       "peers": list(peers)})

@app.route('/attack', methods=['POST'])
def attack():
    '''
    Function to perform three different kinds of attacks:
    - wrong previous hash
    - changing transaction content after calculating the hash of a block
    - reducing difficulty to be the first who has mined
    '''
    
    if not peers:
        return json.dumps({"message":"No peers existing"})
    
    data = request.get_json()
    # data should contain the field attack which specifies which attack: A,B,C,D
    # where A means no attack
 
    global blockchain
    transaction = {
        'author': 'Peter Pan',
        'content': 'A simple default transaction.',
        'timestamp': time.time(),
        'hash': sha256('A simple default transaction.'.encode()).hexdigest()
    }

    last_block = blockchain.get_last_block
    default_block = Block( index=last_block.index + 1,
                           transactions=[transaction],
                           timestamp=time.time(),
                           previous_hash=last_block.hash,
                           miner=request.host_url )

    if data["attack"]=="A":
        # just adds a default correct block
        # JUST NEEDED FOR TEST PURPOSES
        hash_default_block = blockchain.proof_of_work(default_block)
        default_block.hash = hash_default_block

        response = submit_block_to_network(default_block)
        if response["status"]:
            return json.dumps({"message":"Default block was added."})
        else:
            return json.dumps({"message":"Something not working."})
    else:

        tampered_block = default_block

        if data["attack"]=="B":
            # attack where the transaction and the block fields are correct
            # but the attacker used a different last.block as reference
            # thus he is kind of "suggesting" an alternative blockchain
                
            if last_block.index == 0:
                return json.dumps({"message":"Blockchain only has genesis block. No change of previous hash possible."})
            else:
                block = blockchain.retrieve_block(last_block.index-1)
                
                tampered_block.previous_hash = block.hash
                tampered_block.index = block.index
                hash_tampered_block = blockchain.proof_of_work(tampered_block)
                tampered_block.hash = hash_tampered_block

        elif data["attack"]=="C":
            # first calc hash, then change transaction content
            hash_tampered_block = blockchain.proof_of_work(tampered_block)
            tampered_block.hash = hash_tampered_block
            # now the block becomes tampered
            # because if you compute now the hash again, then it will not match with the hash field
            # but recomputing takes too much time for the attacker due to the "difficulty"
            # IS LESS AN ATACK; IT SHOULD SHOW THAT THE CHAIN CAN DETECT SUCH CHANGES
            # ASSUMING AN ATTACKER WHO DOESNT KNOW ABOUT THE WAY BLOCKCHAIN WORKS
            tampered_block.transactions[0]["content"] = "ATTACK"
            tampered_block.transactions[0]["hash"] = sha256('ATTACK'.encode()).hexdigest()
        
        elif data["attack"]=="D":
            # everything fine: previous hash, hash field matches content, BUT the difficulty was decreased
            # to be the first, thus the network should detect that the hash is not having the correct property
            current_diff = blockchain.difficulty
            blockchain.set_difficulty(1)

            hash_tampered_block = blockchain.proof_of_work(tampered_block)
            tampered_block.hash = hash_tampered_block
            
            blockchain.set_difficulty(current_diff)
    
        response = submit_block_to_network(tampered_block)
      
        if not response["status"]:
            # means that the block was not added
            return json.dumps({"block":tampered_block.__dict__,"message":"Tampered block was identified: "+response["message"]})
        else:
            # because we actively sent a uncorrect block, but if this was accepted then something
            # of the proofing alogorithms is not working
            return json.dumps({"message":"Security mechanism is not working"})

@app.route('/modify_difficulty', methods=['POST'])
def modify_difficulty():
    '''
    Set a different difficulty
    '''
    
    diff = request.get_json()["difficulty"]
    global blockchain
    set_diff = blockchain.set_difficulty(int(diff))
    
    if set_diff:
        return diff
    else:
        return "Difficulty unchanged."

def reconstruct_chain(chain_data):
    '''
    Function which takes a Blockchain as a string in json format. From this the function creates
    a Blockchain object and checks if the resulting blockchain is valid (all conditions are fulfilled). 
    This function will be used when a node received a whole blockchain from one of its peers e.g. after being added
    newly to the network.
    '''
    generated_blockchain = Blockchain()
    generated_blockchain.add_genesis_block()
    for idx, block_data in enumerate(chain_data):
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
    The function is looking for the longest chain among all the peers and the nodes own copy. If a longer chain
    is found among the peers, it will take this blockchain for itself.

    Returns a tuple: 
    First field specifying whether a longer chain was found, second field a list of the peers 
    with an invalid blockchain.
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

        # reconstructs the chain AND tests whether it is valid 
        fetched_chain_feedback = reconstruct_chain(chain)

        #fetched_chain_feedback[0] whether the fetched chain was valid or not
        if not fetched_chain_feedback[0]:
            # then in this case fetched_chain_feedback[1] would be a message explaining
            # the error of the invalid block and fetched_chain_feedback[2] would be the index of the 
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

if __name__=="__main__":
    port = sys.argv[1]
    app.run(debug=True,port=port)