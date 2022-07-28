# -*- ENCODING: UTF-8 -*-

"""
Francesco Valentini
Matricola: 0000970197
Email: francesco.valentin11@studio.unibo.it

-------------------------------------------------------------------------------

UDP Client-Server Architecture for File Transfer

-------------------------------------------------------------------------------

SERVER
"""

import atexit
import os
from enum import Enum
from socket import AF_INET, socket, SOCK_DGRAM

# Defining Constants
HOST = ''
PORT = 55555
ADDRESS = (HOST, PORT)
BUFFER_SIZE = 1024
DIRECTORY = '.' + os.sep + 'Files' + os.sep
TIMEOUT = 1

# Creating file storage folder if it's not already there
if not os.path.isdir(DIRECTORY):
    os.makedirs(DIRECTORY)
    print('Created file storage directory')

# Creating Socket
server_socket = socket(AF_INET, SOCK_DGRAM)
server_socket.bind(ADDRESS)


class Command(Enum):
    NONE = '0'
    LIST = '1'
    GET = '2'
    PUT = '3'


class Message(Enum):
    CORRECT = '0'
    INVALID_ERROR = '1'
    COMMUNICATION_ERROR = '2'


class Log(Enum):
    DEFAULT = '0'
    LIST_FILES = '1'
    USER_DOWNLOAD = '2'     # User download from server
    USER_UPLOAD = '3'       # User upload to server
    INVALID = '4'
    ERROR = '5'


# Waits for any requests
def wait_for_requests():
    print('Server opened successfully')
    print('Waiting for any requests...')
    flag = False
    while True:
        try:
            data, client_address = server_socket.recvfrom(BUFFER_SIZE)

            # Decodes message
            data = data.decode('UTF-8')

            # Handles request
            outgoing_message = Command.NONE.value

            # Logs requests
            request_log = Log.DEFAULT

            if data[0] == Command.LIST.value:
                # Lists files
                outgoing_message += list_files()
                request_log = Log.LIST_FILES
            elif data[0] == Command.GET.value:
                # Gets file content and sends it
                outgoing_message += get_file(data[1:], client_address)
                request_log = Log.USER_DOWNLOAD
            elif data[0] == Command.PUT.value:
                # Puts file received from client
                outgoing_message += put_file(data[1:], client_address)
                request_log = Log.USER_UPLOAD
            else:
                # Invalid request
                outgoing_message = Message.INVALID_ERROR.value
                request_log = Log.INVALID
        except:
            # Error during request reception
            outgoing_message = Message.COMMUNICATION_ERROR.value
            request_log = Log.ERROR

        # Sends answer
        server_socket.sendto(outgoing_message.encode('UTF-8'), client_address)

        # Updates request log on command line
        if flag is False:
            flag = True
            print('\nRequest log:')
        if request_log == Log.LIST_FILES:
            print(' - Listed files on server')
        if request_log == Log.USER_DOWNLOAD:
            print(' - Downloaded file from server')
        if request_log == Log.USER_UPLOAD:
            print(' - Uploaded file to server')
        if request_log == Log.INVALID:
            print(' - Invalid request')
        if request_log == Log.ERROR:
            print(' - ERROR')


# Waits for an answer from the client, then returns the message received
def receive(client_address):
    server_socket.settimeout(TIMEOUT)
    while True:
        try:
            data, address = server_socket.recvfrom(BUFFER_SIZE)
        except:
            server_socket.settimeout(None)
            raise Exception
        if address == client_address:
            server_socket.settimeout(None)
            return data.decode('UTF-8')


# Lists all server files
def list_files():
    return str(os.listdir(DIRECTORY))


# Gathers the requested file and sends it to the client
def get_file(file_name, client_address):
    try:
        # Opens file in read mode
        file = open(DIRECTORY + file_name, 'r')
    except:
        # Error while opening file
        return Message.INVALID_ERROR.value
    
    try:
        # Gathers file content and sends it
        message = ''
        for line in file:
            # Sends additional packets if necessary
            if len(message + line) + 2 > BUFFER_SIZE:
                string = Command.NONE.value + Command.GET.value
                server_socket.sendto((string + message).encode('UTF-8'), client_address)
                message = ''
                receive(client_address)
            message += line
    except:
        # Error while sending message
        return Message.INVALID_ERROR.value
    finally:
        file.close()
    # EOF reached: file sent successfully
    return Message.CORRECT.value + message


# Gathers the received file and puts it locally
def put_file(file_name, client_address):
    # Waits for file content
    string = Command.NONE.value
    server_socket.sendto(string.encode('UTF-8'), client_address)
    data = receive(client_address)

    try:
        # Creates a new file
        file = open(DIRECTORY + file_name, 'w')
    except:
        return Message.INVALID_ERROR.value
    
    try:
        # Puts the received content into the new file
        file.write(data[1:])
        # Handling eventual additional packets
        if data[0] == Command.GET.value:
            while True:
                string = Command.NONE.value
                server_socket.sendto(string.encode('UTF-8'), client_address)
                data = receive(client_address)
                file.write(data[1:])
                if data[0] == Command.NONE.value:
                    break
    except:
        # Error while receiving message
        return Message.INVALID_ERROR.value
    finally:
        file.close()
    # File received successfully
    return Message.CORRECT.value


# Shut down server when closing program
atexit.register(server_socket.close)

# Launch program
if __name__ == '__main__':
    wait_for_requests()
