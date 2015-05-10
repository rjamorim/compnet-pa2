Computer Networks Spring 2015
Programming assignment 2
Roberto Amorim - rja2139

This program simulates network-layer routing uwing the Bellman Ford algorithm,
implementing poison reverse.

Cost updates and commands are sent to neighboring nodes using JSON formatted
messages.


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
http://www.markhneedham.com/blog/2013/01/18/bellman-ford-algorithm-in-python/
https://gist.github.com/joninvski/701720
http://pymotw.com/2/json/
https://docs.python.org/2/howto/sockets.html