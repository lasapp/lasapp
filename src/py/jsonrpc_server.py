from jsonrpc import JSONRPCResponseManager # https://pypi.org/project/json-rpc/
import os
import socket

def read_transport_layer(reader):
    header_dict = {}
    line = reader.readline().decode('utf8').rstrip()
    if line == '':
        return None
    while len(line) > 0:
        key, _, val = line.partition(':')
        header_dict[key] = val
        line = reader.readline().decode('utf8').rstrip()

    # print(header_dict)
    message_length = int(header_dict['Content-Length'])
    message_str = reader.read(message_length).decode('utf8')

    return message_str    

def write_transport_layer(writer, response):
    response_utf8 = response.encode('utf8')
    writer.write(f'Content-Length: {len(response_utf8)}\r\n\r\n'.encode('utf8'))
    writer.write(response_utf8)
    writer.flush()

from jsonrpc.jsonrpc2 import JSONRPC20Request, JSONRPC20Response
import json
import dataclasses

class DataclassEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return o.to_dict()
        return super().default(o)
        
def jsonrpc_serialize( data):
    return json.dumps(data, cls=DataclassEncoder)

JSONRPC20Response.serialize = staticmethod(jsonrpc_serialize)
JSONRPC20Request.serialize = staticmethod(jsonrpc_serialize)

def handle_client(reader, writer, dispatcher): 
    while True:
        message_str = read_transport_layer(reader)
        if message_str is None:
            break
        # print('request: ', message_str)
        response = JSONRPCResponseManager.handle(message_str, dispatcher)
        # print('response:', response.json)
        write_transport_layer(writer, response.json)

from typing import Dict, Tuple, Any
from ast_utils.scoped_tree import ScopedTree
_SESSION: Dict[str, Tuple[Any,ScopedTree]] = dict()

def run_server(socket_name, dispatcher):
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(socket_name)
    try:
        while True:
            server.listen(1)
            sock, addr = server.accept()
            print("Hello", sock)
            reader = sock.makefile(mode='rb') # binary
            writer = sock.makefile(mode='wb') # binary
            handle_client(reader, writer, dispatcher)
            reader.close()
            writer.close()
            sock.close()
            _SESSION.clear()
            print("Bye", sock)
    except KeyboardInterrupt:
        print("Interrupt server.")
    finally:
        print("Close server.")
        server.close()
        os.remove(socket_name)