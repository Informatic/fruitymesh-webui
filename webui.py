import json
import logging
import serial
import threading

import flask
import time

logging.basicConfig(level=logging.DEBUG)

PORT = '/dev/serial/by-id/usb-SEGGER_J-Link_XXXXXXXXXXXX-if00'


class ClientThread(threading.Thread):
    ser = None
    daemon = True

    nodes = dict()
    nodes_connections = dict()
    plugged_in_id = None
    last_update = None
    decoder = None

    def run(self):
        self.decoder = json.JSONDecoder()

        while True:
            try:
                if not self.ser:
                    self.ser = serial.Serial(PORT, 38400, timeout=3)

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
        l = self.ser.readline()

        print '>', len(l), repr(l)
        try:
            # FIXME parse multiple messages
            l = l[l.find('{'):]
            msg, _ = self.decoder.raw_decode(l)
            if msg.get('type') == 'device_info':
                msg['lastSeen'] = time.time()
                self.nodes[msg['nodeId']] = msg
            elif msg.get('type') == 'connections':
                self.nodes_connections[msg['nodeId']] = msg
            elif msg.get('type') == 'plugged_in':
                self.plugged_in_id = msg['nodeId']
        except:
            logging.exception('gnuj')

        if not self.last_update or time.time() - self.last_update > 30:
            self.last_update = time.time()

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
    ct.nodes = {}
    ct.nodes_connections = {}
    ct.ser.write('action 0 status get_device_info\r')
    time.sleep(0.5)
    ct.ser.write('action 0 status get_connections\r')
    time.sleep(0.5)
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
    ct.start()
    app.run()


if __name__ == "__main__":
    main()
