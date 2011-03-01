********************
Offline worker usage
********************

Running
=======

``python offlineWorker.py``

Model definition in YAML (JSON) is an input data. to specify file with data
provide it as an unnamed argument to program.

Program generates two output files with names provided in arguments
``-s, --states`` where states will be saved, and ``-c, --cars`` where cars will
be saved. By default names ``states.csv`` and ``cars.csv`` are used.
