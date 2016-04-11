import json
import logging
import threading
import argparse
import time

import serial
import flask

logging.basicConfig(level=logging.DEBUG)



class ClientThread(threading.Thread):
    ser = None
    daemon = True

    nodes = dict()
    nodes_connections = dict()
    plugged_in_id = None

    last_update = None
    update_interval = 30

    decoder = None

    def run(self):
        self.decoder = json.JSONDecoder()

        while True:
            try:
                if not self.ser:
                    self.ser = serial.Serial(self.port, 38400, timeout=3)

                self.process()
            except:
                logging.exception('Process failed')
                time.sleep(2)
                try:
                    self.ser.close()
                except:
                    pass

                self.ser = None

    def process(self):
        l = self.ser.readline().strip()

        if not l:
            return

        print 'recv:', l

        try:
            # FIXME parse multiple messages
            if l.find('{') == -1:
                return

            l = l[l.find('{'):]
            msg, _ = self.decoder.raw_decode(l)
            print '>', msg
            if msg.get('type') == 'device_info':
                msg['lastSeen'] = time.time()
                self.nodes[msg['nodeId']] = msg
            elif msg.get('type') == 'connections':
                self.nodes_connections[msg['nodeId']] = msg
            elif msg.get('type') == 'plugged_in':
                self.plugged_in_id = msg['nodeId']
        except:
            logging.exception('Shit broke')

        if not self.last_update or time.time() - self.last_update > \
                self.update_interval:
            self.last_update = time.time()
            self.do_update()

    def do_update(self):
        self.nodes = dict()
        self.nodes_connections = dict()
        ct.ser.write('\r\r')
        time.sleep(0.5)
        ct.ser.write('action 0 status get_device_info\r')
        time.sleep(0.5)
        ct.ser.write('action 0 status get_connections\r')
        time.sleep(0.5)
        ct.ser.write('get_plugged_in\r')

ct = ClientThread()

app = flask.Flask(__name__)
app.jinja_env.globals.update(zip=zip)


@app.route('/')
def index():
    return flask.render_template(
        'index.html',
        nodes=ct.nodes,
        nodes_connections=ct.nodes_connections,
        plugged_in=ct.plugged_in_id)


@app.route('/update')
def update():
    ct.do_update()
    return flask.redirect('/')


@app.route('/cmd')
def cmd():
    ct.ser.write(flask.request.args.get('q').encode('utf-8') + '\r')
    return flask.redirect('/')


@app.route('/action')
def action():
    for k, v in flask.request.args.items():
        if k.startswith('nodes['):
            cmd = 'action ' + k[6:-1] + ' ' + flask.request.args.get('action')
            ct.ser.write(cmd.encode('utf-8') + '\r')
            time.sleep(0.1)

    return flask.redirect('/')


@app.route('/nodes.json')
def nodes():
    return flask.jsonify(ct.nodes)


def main():
    parser = argparse.ArgumentParser(description='FruityMesh web interface')
    parser.add_argument('--host', default='127.0.0.1', help='HTTP host')
    parser.add_argument('--port', type=int, default=5000, help='HTTP port')
    parser.add_argument('--serial', default='/dev/ttyACM0', help='Serial device')
    args = parser.parse_args()

    ct.port = args.serial
    ct.start()
    app.run(args.host, args.port)


if __name__ == "__main__":
    main()
