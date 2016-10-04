'''This is the "main" file for the to run the cluster manager server

To run the server simply execute the following::

	python3 cluster_manager.py

This will start a new webserver with a UI to connect to all of the agents.

'''
from cluster_manager import app
import requests


@app.route("/", methods=['GET'])
def home():
	return app.send_static_file('index.html')
