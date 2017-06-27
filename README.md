# Virtual-Walker-Network
1.creating the topology of the honest/evil walker network(1 honest region, 1 evil region) using networkx

2.store the topology with a gpickle file

3.creating blocks and cutting corner walkers according to the gpickle file, store relevant data in database

4.send the relevant files (using rsync) to slave machines (machines or virtual machines, specify in config.conf)，the slave machines should have:rsync,libnacl, m2crypto, matplotlib,networkx,configObj. And...enough memory and disk space

5.automatically copy a tracker.conf file into activewalker folder (containing the tracker ip and port)

5.running certain scripts of slave nodes using ansible.

6.Now the virtual walker network is established. Run the activewalker/runwalker.py
  
