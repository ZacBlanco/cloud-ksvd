from cluster_manager import app
from cluster_manager import ws_node_server as ws
def run(prt):
    node_serv = ws.WSThreadedServer('0.0.0.0', prt+1)
    node_serv.start()
    app.run(host='0.0.0.0', port=prt)

if __name__=="__main__":
    run(8080)
