# Computer Networks Spring 2015
# Programming assignment 2
# Roberto Amorim - rja2139

import sys, socket, json, time, os
import select, datetime
from threading import Timer, Thread
from copy import deepcopy
from collections import defaultdict, namedtuple


# Turns address (host + port) into a string, for storage and display
def addr2str(host, port):
    return "{host}:{port}".format(host=host, port=port)


# The opposite of above
def str2addr(string):
    host, port = string.split(':')
    return host, int(port)


# Converts hostname into ip address
def get_host(host):
    return localhost if host == 'localhost' else host


# Returns all neighbors
def get_neighbors():
    return dict([x for x in nodes.iteritems() if x[1]['neighbor']])


# The Bellman-Ford algo. Calculates path costs. Core of the program.
# Called every time the network changes or we receive an update.
def bellman_ford():
    for dest, destination in nodes.iteritems():
        # No need to update our own distance
        if dest != self:
            nexthop = ''
            weight = float("inf")  # cost starts as infinite

            # For each neighbor calculate cheapest route
            for neigh_addr, neigh in get_neighbors().iteritems():
                if dest in neigh['costs']:
                    dist = neigh['direct'] + neigh['costs'][dest]
                    if dist < weight:
                        nexthop = neigh_addr
                        weight = dist

            # Set new calculated cost to the node
            destination['cost'] = weight
            destination['route'] = nexthop


# Sends out calculated costs to all neighbors
def bcast_costs():
    costs = { addr: node['cost'] for addr, node in nodes.iteritems() }
    data = { 'type': COSTSUPDATE }

    for neigh_addr, neighbor in get_neighbors().iteritems():
        # Can't forget to poison reverse!
        poisoned = deepcopy(costs)
        for dest, cost in costs.iteritems():
            if dest not in [self, neigh_addr]:  # If destination is not self nor a neighbor
                if nodes[dest]['route'] == neigh_addr:
                    poisoned[dest] = float("inf")  # Sends cost = infinite for poisoned neighbors

        data['payload'] = {'costs': poisoned}
        data['payload']['neighbor'] = {'direct': neighbor['direct']}
        sock.sendto(json.dumps(data), str2addr(neigh_addr))


# Creates the listener socket
def setup_server(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket!
    try:
        sock.bind((host, port))
        print "Server up, listening on {0}:{1}\n".format(host, port)
    except socket.error, msg:
        print "Error creating listener socket. Maybe the port is already in use?"
        exit(1)
    return sock


def default_node():
    return {'cost': float("inf"), 'neighbor': False, 'route': ''}


# Function that creates new network nodes
def mknode(cost, is_neigh, direct=None, costs=None, addr=None):
    newnode = default_node()
    newnode['cost'] = cost
    newnode['neighbor'] = is_neigh
    newnode['direct'] = direct if direct else float("inf")
    newnode['costs'] = costs if costs else defaultdict(lambda: float("inf"))

    if is_neigh:
        newnode['route'] = addr
        # Check if neighbor is transmitting updates using the resettable timer
        monitor = MonitorTimer(interval=3*run_args.timeout, func=linkdown, args=list(str2addr(addr)))
        monitor.start()  # starts monitoring
        newnode['silence_monitor'] = monitor

    return newnode


# Fuction to provide node information from host and port
def get_node(host, port):
    err = False
    addr = addr2str(get_host(host), port)

    if not in_network(addr):
        err = 'The node is not part of the network'

    node = nodes[addr]
    return node, addr, err

# Commands and updates
LINKDOWN = "linkdown"
LINKUP = "linkup"
LINKCHANGE = "linkchange"
SHOWRT = "showrt"
CLOSE = "close"
COSTSUPDATE = "costsupdate"
SHOWNEIGHBORS = "neighbors"


# Changes link parameters
def linkchange(host, port, **args):
    node, addr, err = get_node(host, port)
    if err:
        return

    # Is there a link between us and the other node?
    if not node['neighbor']: 
        print "There is no direct link to node {0}. Parameters can't be changed\n".format(addr)
        return

    direct = args['direct']
    if direct < 1:
        print "The link cost can not be smaller than 1"
        return

    if 'saved' in node:
        print "This link is down. You must first reactivate it with LINKUP command."
        return

    node['direct'] = direct
    # Updates Bellman-Ford costs
    bellman_ford()


# Deactivates a link
def linkdown(host, port, **args):
    node, addr, err = get_node(host, port)
    if err:
        return

    # Is there a link between us and the other node?
    if not node['neighbor']: 
        print "There is no direct link to node {0}\n".format(addr)
        return

    node['saved'] = node['direct']  # saved gets the cost value, stored in direct
    node['direct'] = float("inf")  # cost becomes infinite
    node['neighbor'] = False  # No longer our neighbor
    node['silence_monitor'].cancel()  # We don't need to monitor if host is up anymore
    # Updates Bellman-Ford costs
    bellman_ford()


# Re-activates a link
def linkup(host, port, **args):
    node, addr, err = get_node(host, port)
    if err:
        return

    # Was this link down previously??
    if 'saved' not in node:
        print "Node {0} is not a neighbor or the link is still up\n".format(addr)
        return

    # Re-activates the link with saved cost
    node['direct'] = node['saved']  # we recover the link cost from "saved"
    del node['saved']  # we remove saved, since that value determines whether the link is down
    node['neighbor'] = True  # The node is our neighbor again!
    # Updates Bellman-Ford costs
    bellman_ford()


# Prints the router's naighbors
def show_neighbors():
    print datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
    print "Router neighbors: "

    for addr, neigh in get_neighbors().iteritems():
        print "{addr}, cost: {cost}, direct: {direct}".format(addr=addr, cost=neigh['cost'], direct=neigh['direct'])
    print ""


# Prints routing info (cost to dest and route taken)
def showrt():
    print datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S")
    print "Router's distance vectors:"

    for addr, node in nodes.iteritems():
        if addr != self:  # We shouldn't print ourselves
            print ("dest: {destination}, cost: {cost}, "
                   "link: {nexthop}").format(destination=addr, cost=node['cost'], nexthop=node['route'])
    print ""


def close():
    sys.exit()


# Figures out if a node is part of the network or not
def in_network(addr):
    if addr not in nodes:
        print 'Node {0} is not part of the network\n'.format(addr)
        return False
    return True


# Just checks if a number is floating point (since .isdigit() doesn't work in this case)
def isfloat(n):
    try:
        float(n)
        return True
    except ValueError:
        return False


# Function that parses the config file
def parse_config(file):
    config = {}
    try:
        with open(file, "rb") as f:
            line = f.readline()
            temp = line.split(' ', 1)

            port = temp[0]
            if port.isdigit():
                if port < 0 or port > 65535:
                    print "ERROR: The port number is outside the acceptable range! (0-65535)"
                    exit(1)
            else:
                print "ERROR: The port number must be a number"
                exit(1)
            config['port'] = int(port)

            timeout = temp[1]
            if isfloat(timeout):
                if timeout < 1:
                    print "ERROR: The timeout value must be higher than 0"
                    exit(1)
            else:
                print "ERROR: The timeout must be a number"
                exit(1)
            config['timeout'] = float(timeout)

            config['neighbors'] = []
            config['costs'] = []
            line = f.readline()
            while line:
                temp = line.split(' ', 1)
                temp2 = temp[0].split(':')

                ip = temp2[0]
                try:
                    socket.inet_aton(ip)
                except socket.error:
                    print "ERROR: The IP address in the config file (" + ip + ") doesn't seem to be valid!"
                    exit(1)
                port = temp2[1]
                if port.isdigit():
                    if port < 0 or port > 65535:
                        print "ERROR: The port number is outside the acceptable range! (0-65535)"
                        exit(1)
                else:
                    print "ERROR: The port number must be a number"
                    exit(1)
                config['neighbors'].append(addr2str(ip, port))

                weight = temp[1]
                if isfloat(weight):
                    if weight < 1:
                        print "ERROR: The link cost can not be smaller than 1"
                        exit(1)
                else:
                    print "ERROR: The cost must be a number"
                    exit(1)
                config['costs'].append(float(weight))

                line = f.readline()
            f.close()
    except:
        print "ERROR: Configuration file can not be read"
        exit(1)
    return config


# Function that parses the user input commands
def parse_input(user_input):
    command = { 'addr': (), 'payload': {} }
    user_input = user_input.split()
    if not len(user_input):
        return { 'error': "Please input a command\n" }
    cmd = user_input[0].lower()

    # Check if it is a valid command
    if cmd not in user_cmds:
        return { 'error': "'{0}' is not a valid command\n".format(cmd) }

    # Check if commands have arguments
    if cmd in [LINKDOWN, LINKUP, LINKCHANGE]:
        args = user_input[1:]
        # validate args
        if cmd in [LINKDOWN, LINKUP] and len(args) != 2:
            return {'error': "'{0}' command requires host and port\n".format(cmd)}
        elif cmd == LINKCHANGE and len(args) != 3:
            return {'error': "'{0}' command requires host, port and cost\n".format(cmd)}

        port = args[1]
        if not port.isdigit():
            if port < 0 or port > 65535:
                return {'error': "The port number is outside the acceptable range! (0-65535)\n"}
            return {'error': "The port number must be a number\n"}
        command['addr'] = (get_host(args[0]), int(port))

        if cmd == LINKCHANGE:
            cost = args[2]
            if not isfloat(cost):
                return {'error': "New weight must be a number\n"}
            command['payload'] = {'direct': float(cost)}

    command['cmd'] = cmd
    return command


# Update costs for a neighbor
def costs_upd(host, port, **args):
    costs = args['costs']
    addr = addr2str(host, port)

    for node in costs:
        if node not in nodes:
            # If a node is not yet in our list of nodes, create it
            nodes[node] = default_node()

    # Node becomes our neighbor!
    if not nodes[addr]['neighbor']:
        print 'New neighbor: {0}\n'.format(addr)
        del nodes[addr]
        nodes[addr] = mknode(cost=nodes[addr]['cost'], is_neigh=True, direct=args['neighbor']['direct'],
                costs=costs, addr=addr)
    else:
        # otherwise just update node costs
        node = nodes[addr]
        node['costs'] = costs
        # restart silence monitor
        node['silence_monitor'].reset()

    # Updates Bellman-Ford costs
    bellman_ford()

updates = {
    LINKDOWN: linkdown,
    LINKUP: linkup,
    LINKCHANGE: linkchange,
    COSTSUPDATE: costs_upd,
}
user_cmds = {
    LINKDOWN: linkdown,
    LINKUP: linkup,
    LINKCHANGE: linkchange,
    SHOWRT: showrt,
    CLOSE: close,
    SHOWNEIGHBORS: show_neighbors,
}


# Creates thread that calls a function in intervals
class Repeater(Thread):
    def __init__(self, interval, target):
        Thread.__init__(self)
        self.target = target
        self.daemon = True
        self.interval = interval
        self.stopped = False
    def run(self):
        while not self.stopped:
            time.sleep(self.interval)
            self.target()


# Creates a resettable timer thread
class MonitorTimer():
    def __init__(self, interval, func, args=None):
        if args != None: assert type(args) is list
        self.interval = interval
        self.args = args
        self.func = func
        self.countdown = self.create_timer()
    def start(self):
        self.countdown.start()
    def create_timer(self):
        t = Timer(self.interval, self.func, self.args)
        t.daemon = True
        return t
    def cancel(self):
        self.countdown.cancel()
    def reset(self):
        self.countdown.cancel()
        self.countdown = self.create_timer()
        self.start()


if __name__ == '__main__':
    localhost = socket.gethostbyname(socket.gethostname())
    conffile = ""
    if not os.path.isfile(sys.argv[1]):
        print "ERROR: Invalid file name for configuration file"
        exit(1)
    else:
        conffile = sys.argv[1]

    parsed = parse_config(conffile)
    RunArgs = namedtuple('RunInfo', 'port timeout neighbors costs')
    run_args = RunArgs(**parsed)

    # Here we create a list of all nodes in the network
    nodes = defaultdict(lambda: default_node())
    for neighbor, cost in zip(run_args.neighbors, run_args.costs):
        nodes[neighbor] = mknode(cost=cost, direct=cost, is_neigh=True, addr=neighbor)

    # Initiate UDP socket
    sock = setup_server(localhost, run_args.port)

    # My own cost should be zero
    self = addr2str(*sock.getsockname())
    nodes[self] = mknode(cost=0.0, direct=0.0, is_neigh=False, addr=self)

    # Broadcast costs
    bcast_costs()
    Repeater(run_args.timeout, bcast_costs).start()

    inputs = [sock, sys.stdin]
    # The loop that reads updates
    while True:
        in_ready, out_ready, except_ready = select.select(inputs, [], [])
        for s in in_ready:
            if s == sys.stdin:
                # This is local user input
                parsed = parse_input(sys.stdin.readline())

                if 'error' in parsed:
                    print parsed['error']
                    continue

                cmd = parsed['cmd']
                if cmd in [LINKDOWN, LINKUP, LINKCHANGE]:
                    data = json.dumps({ 'type': cmd, 'payload': parsed['payload'] })
                    sock.sendto(data, parsed['addr'])

                user_cmds[cmd](*parsed['addr'], **parsed['payload'])
            else: 
                # This is a message from a remote node
                data, sender = s.recvfrom(4096)
                loaded = json.loads(data)
                update = loaded['type']
                payload = loaded['payload']

                if update not in updates:
                    print "'{0}' is not a valid update message\n".format(update)
                    continue

                updates[update](*sender, **payload)
    sock.close()
