#!/usr/bin/python2

#z5062107 MATTHEW Y F CHEN

from socket import *
from time import sleep
import sys
import re
from collections import defaultdict
import os
import random
import time
from decimal import Decimal

node_ID = 0;
node_port = 0;

""" 
* This program is executed many times with a text file ./ass2.py A (node ID) 12000 (port number) configA.txt (text file containing info)
* The program will then send link-state packets around to every other node on the port, forwarding packets so everyone has sent a packet 
* and received a packet from everyone else.

* Each node will then run dijsktra on the map created by looking at all the packet information received.
* The node will then output shortest distance to each node as well as path


* Harder part: If a node fails the other nodes have to detect this in the next phase of sending link-state packets (every 30 seconds)

* My comments: Overall, a relatively straight-forward assignment, however considering I didn't know Python well it was slightly more difficult. The most time-consuming things were 
* writing my own dijkstra which was enjoyable. My solution to the hard part (nodes dropping out) was pretty straight-forward; I just treated each phase independently and built up
* new nodes every time (very inefficient for scaling) but in this context it worked well. I got a mark of 10/10 for this completing both parts to the assignment.

* I regret this implementation heavily, it is too complex and vague looking back, the hashes have almost identical names as well...
* In my defence the second part of the assignment (which caused me to make many more hashes) was due very soon and I had other things pending, however 
* admittedly some hashes are not that necessary.

"""


full_graph = {}
weight = {}   
all_messages = {}
all_nodes = {}      
path = {}
neighbours_hash = {}        
nodes = {}
complete_list = {}
distances = {} 
visited = {}

neighbours = []
temp_array = []
listening_ports = []

IP = 0;
route_update_interval = 30;	        #dijkstra every 30
update_interval = 1;	            #send link state packets every second
sender_router = "Z"


next_nodes = []
temp_nodes = []


def initialise():   #   Create initial conditions (what my node is in reach of, etc.) and read file

    temp_file = open(sys.argv[3])
    
    num_lines = int(temp_file.readline())   
    i = 0
    
    for i in range(0, num_lines):      
        temp_string = temp_file.readline()      
        temp_array = temp_string.split()
        
        listening_ports.append(temp_array[2])  
        neighbours.append(temp_array[0])
        
        temp_decimal = Decimal(float(temp_array[1]))
        rounded_decimal = round(temp_decimal, 2)
        weight[temp_array[0]] = rounded_decimal
         
    temp_file.close()
    

    return;

def print_graph(g): #print the graph (node1, node2, weight)

    for v in g:
        for w in v.get_connections():
            vid = v.get_id()
            wid = w.get_id()
            print '( %s , %s, %3lf)'  % ( vid, wid, v.get_weight(w))

    for v in g:
        print 'g.vert_dict[%s]=%s' %(v.get_id(), g.vert_dict[v.get_id()])
        
    return;

def create_packet():        #   Packet creation

    #the link state packet should contain the router's neighbours
    #packet starts with identity of sender, followed by sequence number and age
    #layout:
    
    #--------
    #Version: 1.1
    #Root router: A
    #Sender router: node_ID
    #Sequence number: 231
    #Age: 0 <-- append this
    #Root neighbours: A5, D2, E3, F1 (numbers represent weight)
    #Link IP: 127.0.0.1
    #Length of packet: 25
    #--------
        
    random.seed(time.time()) 
    seq_number = random.randrange(0, 150);
    temp_neighbours = "Link neighbours: "
    
    for v in weight:
        temp_neighbours = temp_neighbours + v + repr(weight[v]) + " "
    
    temp_neighbours = temp_neighbours + "\n"  
    
    packet = ("--------\nVersion: 1.1\nRoot router: " + node_ID + "\nSender router: " + node_ID + "\nSequence number: " + repr(seq_number) + "\n" + "Age: 0\n" + temp_neighbours + "Link IP: 127.0.0.1\nPacket length = ")
    
    temp_length = len(packet)
    
    packet = packet + repr(temp_length) + "\n--------\n"
    #print packet
    

    return packet;
    
def send_packets(number, graph):

    #send initial packet
    i = 0
    all_nodes = len(neighbours)
    message_sent = create_packet()
    all_messages[node_ID] = 1 
    serverSocket.settimeout(5)
    
    #initial broadcast, then wait for packets to rebroadcast

    for i in range(0, all_nodes):
        serverSocket.sendto(message_sent, ('127.0.0.1', int(listening_ports[i])))  

    temp_start = time.time()
    
    while time.time() - temp_start < 7.5:
        try:
           message_received = serverSocket.recv(1024)
        except:
            break;
        else:
            rebroadcast(message_received)

    print "------"

    return;

def create_graph(graph):

    global complete_list;

    graph.add_vertex(node_ID)
 
    for v in nodes:        ###U FOOL, all the nodes didnt exist yet
        if (complete_list.has_key(v) == 0):
            graph.add_vertex(v)     #this is what happened, made A, gave BCD edges, BCD not alive
            complete_list[v] = 1; 
            

    for v in full_graph:
        temp_string = full_graph[v].split( ) 
        for temp in range(0, len(temp_string)):
            if (check_duplicates(graph, v, temp_string[temp][0:1]) == 0): 
                graph.add_edge(v, temp_string[temp][0:1], float(temp_string[temp][1:4]))
    print "Nodes alive: "
    print g.get_vertices()
    dijkstra(g)        
    
    return;

def dijkstra(graph):

    global visited, temp_nodes;
    
    distances[node_ID] = 0
    visited[node_ID] = 1
    
    for temp in graph.get_vertices():       #initialise all the distances
        path[temp] = node_ID
        if temp != node_ID:
            distances[temp] = 99999;
            visited[temp] = 0
            all_nodes[temp] = 0
    
#strategy, have array for each node, if each node has had dijkstra called on it, then we end
    
    temp_nodes.append(node_ID)
    all_nodes[node_ID] = 1
    
    while (check_all() == 0):
        for temp_node in range(0, len(temp_nodes)):
            all_nodes[temp_nodes[temp_node]] = 1
            base_node = graph.get_vertex(temp_nodes[temp_node]) 
                
            if (temp_nodes[temp_node] == node_ID or is_adjacent(graph, node_ID, temp_nodes[temp_node]) == 0):
                length = len(base_node.get_connections())
            else:
                length = len(base_node.get_connections()) - 1
              
            for temp in range(0, length):
                next_node_letter = find_minimum(graph, temp_nodes[temp_node])
                next_node = graph.get_vertex(next_node_letter)
                if (distances[temp_nodes[temp_node]] + base_node.get_weight(next_node) < distances[next_node_letter]):
                    distances[next_node_letter] = distances[temp_nodes[temp_node]] + base_node.get_weight(next_node)
                    path[next_node_letter] = path[temp_nodes[temp_node]] + next_node_letter 
                visited[next_node_letter] = 1
                
                next_nodes.append(next_node_letter)
            reset_visited(graph, temp_nodes[temp_node])
            
        del temp_nodes[:]
        temp_nodes = next_nodes[:]
        del next_nodes[:]  
      
    for temp in distances:
        if (temp != node_ID):
            print "least-cost path to node " + temp + ": " + path[temp] + " and the cost is " + repr(distances[temp]) 
            
    distances.clear()
    path.clear()
    visited.clear()
    del temp_nodes[:]
    del next_nodes[:]
    sleep(1)
    
    return;

def is_adjacent(graph, node1, node2):   #returns 1 if adjacent, 0 otherwise

    temp_node = graph.get_vertex(node1)
    for temp in temp_node.get_connections():
        if temp.id == node2:
            return 1;
    
    return 0;
    


def check_all():
    
    return_value = 1
    for temp in all_nodes:
        if (all_nodes[temp] == 0):
            return_value = 0
            break;
    
    return return_value

def reset_visited(graph, last_node):
    
    for temp in graph.get_vertices():       #initialise all the distances
        if temp != node_ID and temp != last_node:
            visited[temp] = 0

    return;

def find_minimum(graph, node): #find node to go to

    minimum = 99999;
    minimum_node = 'Z';
    new_node = graph.get_vertex(node)
    for temp in new_node.get_connections():
        if (visited[temp.id] == 0): #if hasn't visited yet
            if (new_node.get_weight(temp) < minimum):
                minimum = new_node.get_weight(temp)
                minimum_node = temp.id            


    return minimum_node;
    
def check_duplicates(graph, node1, node2):      #check duplicates within graph because graph implementation doesn't have it

    duplicate = 0

    check_duplicate = graph.get_vertex(node1)
    if (check_duplicate != None):
        for check_counter in check_duplicate.get_connections():
            if check_counter.id == node1:
                duplicate = 1
                break;   
            
    return duplicate;

def rebroadcast(message):
    
    new_message = recreate(message)             #change the message after receiving it
    if all_messages.has_key(sender_router):     #if rebroadcasted already, dont again
        return;                                 #at the end we should broadcast ABCDEF once each, we may receive many of one but we never rebroadcast
    else:   
        all_nodes = len(neighbours)
        for i in range(0, all_nodes):
            if (neighbours[i] != sender_router): #if it's not the one it has came from
                serverSocket.sendto(new_message, ('127.0.0.1', int(listening_ports[i])))

        all_messages[sender_router] = 1

    return;

def recreate(message):

    global sender_router;

    #some searches to reconstruct my new message

    searchObj = re.search( r'Root router: (.*)', message, re.M|re.I)
    if searchObj:
        nodes[searchObj.group(1)] = 1
        sender_replace = searchObj.group(1)
        sender_router = searchObj.group(1)
    
    searchObj2 = re.search( r'Age: (.*)', message, re.M|re.I)
    if searchObj2:
        age_replace = int(searchObj2.group(1)) + 1
        
    searchObj3 = re.search( r'Link neighbours: (.*)', message, re.M|re.I)
    if searchObj3:
        neighbours_constant = searchObj3.group(1)
    
    searchObj4 = re.search( r'Sequence number: (.*)', message, re.M|re.I)
    if searchObj4:
        sequence_constant = searchObj4.group(1) 
        
    searchObj5 = re.search( r'Sender router: (.*)', message, re.M|re.I)
    if searchObj5:
        neighbours_hash[searchObj5.group(1)] = 1;   
    
    packet = ("--------\nVersion: 1.1\nRoot router: " + sender_router + "\nSender router: " + node_ID + "\nSequence number: " + sequence_constant + "\n" + "Age: "+ repr(age_replace) + "\nLink neighbours: " + neighbours_constant + "\nLink IP: 127.0.0.1\nPacket length = ")  
    
    full_graph[sender_router] = neighbours_constant
    temp_length = len(packet)
    
    packet = packet + repr(temp_length) + "\n--------\n"    
        
    return packet

class Vertex:
    def __init__(self, node):
        self.id = node
        self.adjacent = {}

    def __str__(self):
        return str(self.id) + ' adjacent: ' + str([x.id for x in self.adjacent])

    def add_neighbor(self, neighbor, weight=0):
        
        self.adjacent[neighbor] = weight

    
    def get_connections(self):
        return self.adjacent.keys()  

    def get_id(self):
        return self.id

    def get_weight(self, neighbor):
        return self.adjacent[neighbor]

class Graph:
    def __init__(self):
        self.vert_dict = {}
        self.num_vertices = 0

    def __iter__(self):
        return iter(self.vert_dict.values())

    def add_vertex(self, node):
        self.num_vertices = self.num_vertices + 1
        new_vertex = Vertex(node)
        self.vert_dict[node] = new_vertex
        return new_vertex

    def get_vertex(self, n):
        if n in self.vert_dict:
            return self.vert_dict[n]
        else:
            return None

    def add_edge(self, frm, to, cost = 0):
        if frm not in self.vert_dict:
            return;
        if to not in self.vert_dict:
            return;
        self.vert_dict[frm].add_neighbor(self.vert_dict[to], cost)
        self.vert_dict[to].add_neighbor(self.vert_dict[frm], cost)

    def get_vertices(self):
        return self.vert_dict.keys()


if __name__ == "__main__":

    #two arguments, NODE ID and NODE_PORT
    
    if (len(sys.argv) != 4):
        sys.stderr.write("<ass2.py> ./new.py NODE_ID NODE_PORT TEXT_FILE\n")
    else:
        node_ID = sys.argv[1]
        node_port = int(sys.argv[2])
        text_file = sys.argv[3]
        IP = "127.0.0.1"
        
        g = Graph()
    
        serverSocket = socket(AF_INET, SOCK_DGRAM)
        serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        serverSocket.bind((IP, node_port))   
        
        ###for timing###
        initialise()
        
        #starting time of program
        time_start = time.time()
        timer_counter = 0
        
        route_update_interval = 30
        
        while 1:
            if (time.time() - time_start >= update_interval):
                initialise()
                packet_sent = create_packet()
                send_packets(packet_sent, g)
                timer_counter = timer_counter + 1
                time.start = time.time()         
                create_graph(g) 
                empty_graph = Graph()
                g = empty_graph
                del listening_ports[:]
                del neighbours[:]
                weight.clear()
                neighbours_hash.clear()
                complete_list.clear()
                nodes.clear()
                all_messages.clear()
        
        serverSocket.close()


