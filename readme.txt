Computer Networks Spring 2015
Programming assignment 2
Roberto Amorim - rja2139

This program simulates network-layer routing uwing the Bellman Ford algorithm,
implementing poison reverse.

Updates are sent to neighboring nodes using JSON formatted messages.


Running the program:
$ python bfclient.py client0.txt

    where client0.txt is the configuration file following the formatting proposed
    in the assignment notes


The available commands are:
LINKDOWN: destroys a link
LINKUP: restores a link
CHANGECOST: changes cost for a link
SHOWRT: show the routing table
CLOSE: kills the node immediately, simulating a hardware failure


References:
http://en.wikipedia.org/wiki/Bellman%E2%80%93Ford_algorithm
http://www.markhneedham.com/blog/2013/01/18/bellman-ford-algorithm-in-python/
https://gist.github.com/joninvski/701720
