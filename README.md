FruityMesh-Webui
================

Really simple FruityMesh debugging GUI written in Python / Flask written in 30
minutes out of plain boredom.

Installation
------------
Everyting needed is in `requirements.txt`. Just run:

    pip install -r requirements.txt
    python webui.py

Usage
-----
 - "Action" button sends provided action command to selected nodes (eg. `io led
   on`)
 - "Update" forces update (data is auto-updated every 30 seconds)
 - "Enable/disable rssi" enables `status` module which collects RSSI data for
   all nodes
 - "LED on / off" is self-explanatory

UI uses outside-hosted visjs and bootswatch assets. Sorry.

License
-------
MIT
