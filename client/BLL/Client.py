import sys
sys.path.append("./Client")
from api.IResponse import IResponse
from socket import *
import json
from select import *
import select
from  .Validation import *
import os
from datetime import datetime
from os import path
from api.IClient import *
from api.IFriends import IFriend
from api.IRequest import IRequest

class Request(IRequest):
    def __init__(self, header: dict = {}, body: dict = {}, req: str = "", fileName: str = "", user: str = "", password: str = "", origin: str = "", toClient: str = "", *args, **kwargs) -> None:
        super().__init__(header,body,req,fileName,user,password,origin,toClient,*args,**kwargs)
        
    def get_req(self):
        return self.header.get("req")

    def get_data(self):
        return self.body.get("data")

    def get_origin(self):
        return self.origin

    def get_date(self):
        return self.header.get("date")

    def get_user(self):
        form: dict = self.body.get("form")
        return form.get("user")

    def get_password(self):
        form: dict = self.body.get("form")
        return form.get("password")

    def get_toClient(self):
        return self.body.get("to")

    def __str__(self):
        return json.dumps({"header": self.header, "body": self.body, "origin": self.origin})

class Response(IResponse):

    def __init__(self, header: dict = {}, body: dict = {}, res: str = "", origin: str = "", *args, **kwargs) -> None:
        self.header = header if header else {
            "res": res, "date": str(datetime.now())}
        self.body = body if body else {"args": args, "data": kwargs}
        self.origin = origin

    def get_res(self):
        return self.header.get("res")

    def get_data(self):
        return self.body.get("data")

    def get_origin(self):
        return self.origin

    def get_date(self):
        return self.header.get("date")

    def get_body(self):
        return self.body

    def __str__(self):
        return json.dumps({"header": self.header, "body": self.body, "origin": self.origin})

class Friend(IFriend):

    def __init__(self, name: str, isConnect: bool, path_folder: str) -> None:
        super().__init__(name,isConnect,path_folder)

    def write(self, *args, **kwargs):
        filename = self.msg_file if args[0] == "msg"else self.log_file

        listObj = []
        try:
            with open(filename) as file:
                listObj = json.load(file)
            listObj.append(kwargs)
            with open(filename, 'w') as json_file:
                json.dump(listObj, json_file,
                          indent=4,
                          separators=(',', ': '))
        except:
            pass

    def read(self, filename: str, f=0, to=10):
        file_Name = self.msg_file if filename == "msg"else self.log_file
        listObj = []
        try:
            with open(file_Name) as file:
                listObj = json.load(file)
                listObj = listObj[::-1]
                length = len(listObj)
            return listObj[:14], f, to
            # if length < to:
            #     return listObj[length-10:length], length-10, length
            # return listObj[f:to], f, to
        except:
            return [], f, to

    def __repr__(self):
        return f"{self.name} {self.isConnect}"

class Client(Iclient):

    def __init__(self, id: int = 1, name: str = f"user", port: int = 3000, host: str = "localhost") -> None:
        super().__init__()
        self.id = id
        self.connectedTCP: bool = False
        self.connectedUDP: bool = False
        self.name = name
        self.port = port
        self.host = host
        self.path = ""
        self.friends_list = []
        self.friends: dict[str, Friend] = {}
        self._socket_TCP = socket(AF_INET, SOCK_STREAM)
        self._socket_UDP = socket(AF_INET, SOCK_DGRAM)
        self.options: dict[str, function] = {}
        self.load_options()

    def load_options(self):
        self.options["udpateFriend"] = self.udpateFriend
        self.options["brodcast"] = self.brodcast
        self.options["msg"] = self.get_msg

    def connect_to_TCP(self) -> bool:
        try:
            self._socket_TCP.connect((self.host, self.port))
            print("The connection was successful (TCP)")
            self.connectedTCP = True
            return True
        except:
            print("The connection failed (TCP)")
            return False

    def connect_to_UDP(self):
        try:
            self._socket_UDP.connect((self.host, self.port))
            print("The connection was successful (UDP)")
            self.connectedUDP = True
            return True
        except:
            print("The connection failed (UDP)")
            return False

    def close_connection_TCP(self):
        try:
            self._socket_TCP.close()
            print("The close connection was successful (TCP)")
            self.connectedTCP = False
            return True
        except:
            print("The close connection failed (TCP)")
            return False

    def close_connection_UDP(self):
        try:
            self._socket_UDP.close()
            print("The close connection was successful (UDP)")
            self.connectedUDP = False
            return True
        except:
            print("The close connection failed (UDP)")
            return False

    def create_data_directory(self):
        self.path = "./client/data/"+self.name
        if not path.isdir(self.path):
            os.mkdir(path.join("./client/data", self.name))

    def create_data_directory_friends(self, data: dict):
        friends_list = data.get("listOnline")
        friends_list.remove(self.name)

        if len(self.friends_list) == 0:
            self.friends_list: list[str] = os.listdir(path=self.path)

        for name in self.friends_list:
            path_folder = path.join(self.path, name)
            if name in friends_list:
                friends_list.remove(name)
                self.friends[name] = Friend(name, True, path_folder)
                continue
            self.friends[name] = Friend(name, False, path_folder)

        for friend in friends_list:
            path_folder = path.join(self.path, friend)
            os.mkdir(path_folder)
            self.friends[friend] = Friend(friend, True, path_folder)

        self.friends = {k: v for k, v in sorted(
            self.friends.items(), key=lambda item: not item[1].isConnect)}

    def login(self, req: str = "", password: str = "", origin: str = "", *args, **kwargs):
        request = Request(header={"req": req}, user=self.name,
                          password=password, origin=origin, *args, **kwargs)
        try:
            self._socket_TCP.send(request.__str__().encode())
            print(f"Sent message \"{request}\"\n")
        except Exception as e:
            print(f"fail send \"{request}\"\n")
            print("Error msg :", e)
            return False, "error connect"
        try:
            response_string = self._socket_TCP.recv(4096).decode()
            response_dict = json.loads(response_string)
            response_object = Response(**response_dict)
            print(f"Got response\"{response_object}\"\n")
            if response_object.get_res() == "Success":
                self.create_data_directory()
                self.create_data_directory_friends(response_object.get_data())
                return True, response_object.get_res()
        except Exception as e:
            print("No response from server ", e)
            return False, "IoException"
        return False, response_object.get_res()

    def register(self, req: str = "", password: str = "", origin: str = "", *args, **kwargs):
        request = Request(header={"req": req}, user=self.name, password=password,
                          origin=origin, *args, **kwargs)
        try:
            self._socket_TCP.send(request.__str__().encode())
            print(f"Sent message \"{request}\"\n")
        except:
            print(f"fail send \"{request}\"\n")
            return False, "error"
        try:
            response_string = self._socket_TCP.recv(1024).decode()
            response_dict = json.loads(response_string)
            response_object = Response(**response_dict)
            print(f"Got response\"{response_object}\"\n")
            if response_object.get_res() == "available":
                return True, "Success"
        except:
            print("No response from server")
            return False, "IoException"
        return False, response_object.get_res()

    def readTCP(self, connection):
        if connection is self._socket_TCP:
            self.server_response(connection)

    def readUDP(self, connection):
        pass

    def server_response(self, connection):
        try:
            response_string = connection.recv(4096).decode()
        except:
            pass
        if response_string:
            print(f"Got response\"{response_string}\"\n")
            response_dict = json.loads(response_string)
            response_object = Response(**response_dict)
            res = response_object.get_res()
            self.options[res](response_object)

    def udpateFriend(self, res: Response):
        self.mc += 1
        self.create_data_directory_friends(res.get_data())

    def brodcast(self):
        pass

    def get_msg(self, res: Response):
        self.mc += 1
        body = res.get_body()
        data: dict = res.get_data()
        msg = data.get("msg")
        form: dict = body.get("form")
        nameFriend = form.get("user")
        self.friends.get(nameFriend).write("msg", msg=msg)

    def request(self, req: str = "", fileName: str = "",  password: str = "", origin: str = "", toClient: str = "", *args, **kwargs):
        request = Request(req=req, fileName=fileName, user=self.name, password=password,
                          origin=origin, toClient=toClient, *args, **kwargs)
        try:
            self._socket_TCP.send(request.__str__().encode())
            print(f"Sent message \"{request}\"\n")
        except:
            print(f"fail send \"{request}\"\n")
            return False, "error"

    def response(self):
        inputs = [self._socket_TCP, self._socket_UDP]
        outputs = []
        while self.connectedTCP:
            readable, writable, exceptional = select.select(
                inputs, outputs, inputs, 0.1)
            for s in readable:
                s: socket
                if s.proto == self._socket_TCP.proto:
                    self.readTCP(s)
                elif s.proto == self._socket_UDP.proto:
                    self.readUDP(s)

    def __del__(self):
        self.connectedTCP = False
        self.connectedUDP = False
        self.close_connection_UDP()
        self.close_connection_TCP()
        print("Client destroyed, Goodbye!")

    def __str__(self) -> str:
        return f"id {self.id}\nname {self.name}\nport {self.port}\nhost {self.host}"