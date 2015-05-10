Computer Networks Spring 2015
Programming assignment 2
Roberto Amorim - rja2139

This program simulates network-layer routing uwing the Bellman Ford algorithm,
implementing poison reverse.


Cost updates and commands are sent to neighboring nodes using JSON formatted
messages.

The program starts by reading the configuration in the provided file and loading
the parameters within. It starts listening in the port provided and sends updates
to all listed neighbors at the defined intervals. It uses the updates it received
to build its own routing table.

It also starts listening at the command line for commands from the user. Commands
are checked and, if validated, they are executed. The link down command cause
links to be disabled (cost is set to infinity) on both ends of the link (a message
is sent to the remote host with the same command) and a recalculation of the
Bellman-Ford weights is triggered

link up command has the opposite effect: the link is reenabled on both sides using
a stored cost value, and again a Bellman-Ford recalculation is triggered.

changecost changes the cost of a link and triggers the Bellman-Ford algorithm to
update the routing tables reflecting the new cost.

showrt displays the routing table in use by the node at that moment

close simulates a node hardware failure, making it go down immediately without
warning neighbouring nodes.

Reverse poisoning is implemented to indicate to other routers that a route is no
longer reachable and should not be considered from their routing tables


Running the program:
$ python bfclient.py client0.txt

    where client0.txt is the configuration file following the formatting proposed
    in the assignment notes

    I created some configuration files using five machines from CLIC, and they can
    be used to evaluate the program. The files are:
    london.txt
    moscow.txt
    paris.txt
    sofia.txt
    warsaw.txt


The available commands are:
linkdown: destroys a link
linkup: restores a link
changecost: changes cost for a link
showrt: show the routing table
close: kills the node immediately, simulating a hardware failure


References:
http://en.wikipedia.org/wiki/Bellman%E2%80%93Ford_algorithm
http://en.wikipedia.org/wiki/Route_poisoning
http://www.markhneedham.com/blog/2013/01/18/bellman-ford-algorithm-in-python/
https://gist.github.com/joninvski/701720
http://pymotw.com/2/json/
https://docs.python.org/2/howto/sockets.html
