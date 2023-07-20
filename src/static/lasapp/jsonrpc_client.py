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
import dataclasses
import json

class DataclassEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return o.to_dict()
        return super().default(o)
        
def jsonrpc_serialize( data):
    return json.dumps(data, cls=DataclassEncoder)

JSONRPC20Response.serialize = staticmethod(jsonrpc_serialize)
JSONRPC20Request.serialize = staticmethod(jsonrpc_serialize)

import uuid
import socket

class _Method():
    def __init__(self, func, name):
        self.func = func
        self.name = name
    
    def __call__(self, **kwargs):
        # print(self.name, kwargs)
        object_hook = kwargs.pop("object_hook", None)
        response = self.func(self.name, kwargs)
        if object_hook is not None:
            if isinstance(response["result"], list):
                return [object_hook(el) for el in response["result"]]
            else:
                return object_hook(response["result"])
        return response
        

class JSONRPC_Client:
    def __init__(self, sock, reader, writer):
        self.sock = sock
        self.reader = reader
        self.writer = writer

    def close(self):
        self.reader.close()
        self.writer.close()
        # self.sock.shutdown()
        self.sock.close()
        # await self.writer.wait_closed()

    def send_request(self, method, params):
        request = JSONRPC20Request(
            method=method,
            params=params,
            _id=str(uuid.uuid4()),
            is_notification=False
        )

        write_transport_layer(self.writer, request.json)

        response = read_transport_layer(self.reader)
        response = JSONRPC20Response.deserialize(response)
        if "error" in response:
            raise Exception(response["error"]["message"] + ": " + str(response["error"]["data"]))
        return response
    
    def __getattr__(self, name):
        return _Method(self.send_request, name)



def get_jsonrpc_client(socket_name):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(socket_name)
    reader = sock.makefile(mode='rb') # binary
    writer = sock.makefile(mode='wb') # binary

    return JSONRPC_Client(sock, reader, writer)

            