# -*- ENCODING: UTF-8 -*-

"""
Francesco Valentini
Matricola: 0000970197
Email: francesco.valentin11@studio.unibo.it

-------------------------------------------------------------------------------

UDP Client-Server Architecture for File Transfer

-------------------------------------------------------------------------------

CLIENT
"""

import os
import sys
from enum import Enum
from socket import AF_INET, socket, SOCK_DGRAM
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.font import Font
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import Combobox


class Command(Enum):
    NONE = '0'
    LIST = '1'
    GET = '2'
    PUT = '3'


class Message(Enum):
    CORRECT = '0'
    INVALID_ERROR = '1'
    COMMUNICATION_ERROR = '2'


# Gather server info
print('Server configuration (double-type ENTER key to use defaults)')
HOST = input('HOST: ')
if not HOST:
    # Default host
    HOST = 'localhost'
    sys.stdout.write("\033[F")  # Cursor up one line
    print('HOST: ' + HOST)
PORT = input('PORT: ')
if not PORT:
    # Default port
    PORT = 55555
    sys.stdout.write("\033[F")  # Cursor up one line
    print('PORT: ' + str(PORT))
else:
    # Parsing string as an integer
    PORT = int(PORT)
print('Opening client')

# Defining constants
BUFFER_SIZE = 1024
SERVER_ADDRESS = (HOST, PORT)
DIRECTORY = '.' + os.sep + 'Files' + os.sep

# Creating socket
client_socket = socket(AF_INET, SOCK_DGRAM)


# Closing behavior: destroy window and shut down client
def on_close():
    window.destroy()
    client_socket.close()


# Switches frame: raises the desired one to the top, hiding below ones
def raise_frame(frame):
    frame.tkraise()
    # Change window title depending on the frame
    if frame.winfo_name() == 'menu':
        window.title('UDP File Transfer')
    elif frame.winfo_name() == 'list':
        window.title('File List')
    elif frame.winfo_name() == 'download':
        window.title('File Download')
    elif frame.winfo_name() == 'upload':
        window.title('File Upload')


# Goes back to menu frame and destroys the old frame
def back(frame):
    raise_frame(create_menu_frame())
    frame.destroy()


# Sends a message to the server
def send(message):
    client_socket.sendto(message.encode('UTF-8'), SERVER_ADDRESS)


# Receives a message from the server and handles it
def receive():
    try:
        # TODO: fix message strings
        data, server_address = client_socket.recvfrom(BUFFER_SIZE)
        data = data.decode('UTF-8')
    except:
        data = 'ERROR: Reception of server message'

    if data[0] == Message.INVALID_ERROR.value:
        data = 'ERROR: Invalid request sent'
    elif data[0] == Message.COMMUNICATION_ERROR.value:
        data = 'ERROR: Message not sent: Unexpected communication error'
    if not data[0] == Message.CORRECT.value:
        messagebox.showerror('Error', data)
        raise Exception(data)

    return data[1:]


# Makes get request
def get(file_name, message_label):
    # Checks if file name is an empty string
    if file_name == '':
        message_label.config(text='File name cannot be empty')
        return

    # Sends request
    send(Command.GET.value + file_name)

    # Gets answer
    data = receive()

    # Launches error message
    if data[0] == Message.INVALID_ERROR.value:
        message_label.config(text='ERROR: Could not read file "' + file_name + '"')
        return

    try:
        # Opens a new file
        file = open(file_name, 'w')
    except:
        message_label.config(text='ERROR: File download went wrong')

    try:
        # Puts received content in the new file
        file.write(data[1:])
        if data[0] == Command.GET.value:
            while True:
                send('')
                data = receive()
                if data[0] == Message.INVALID_ERROR.value:
                    raise Exception
                file.write(data[1:])
                if data[0] == Command.NONE.value:
                    break
    except:
        message_label.config(text='ERROR: Downloading file from server')
        return
    finally:
        file.close()
    message_label.config(text='Download completed successfully')


# Makes put request
def put(file_path, message_label):
    # Checks if file name is an empty string
    if file_path == '':
        message_label.config(text='File path cannot be empty')
        return

    # Opens the requested file
    try:
        file = open(file_path, 'r')
    except:
        message_label.config(text='ERROR: Could not read file "' + file_path + '"')
        return

    # Sends request with file name
    split_path = file_path.split(os.sep)
    send(Command.PUT.value + split_path[len(split_path) - 1])
    receive()

    # Gets and sends file content
    try:
        message = ''
        for line in file:
            # Sends additional packets if necessary
            if len(message + line) + 1 > BUFFER_SIZE:
                send(Command.GET.value + message)
                message = ''
                data = receive()
            message += line
    except IOError:
        message_label.config(text='Could not read file "' + file_path + '"')
        return
    except:
        message_label.config(text='ERROR: Uploading file to server')
        return
    # EOF reached: file sent successfully
    send(Command.NONE.value + message)

    # Get and write the response
    data = receive()
    if data[0] == Message.CORRECT.value:
        data = 'Upload completed successfully'
    elif data[0] == Message.INVALID_ERROR.value:
        data = 'ERROR: Uploading file to server'
    else:
        data = 'ERROR: Could not decode protocol'
    message_label.config(text=data)


# Gathers the raw list from server and creates list of file names
def get_file_list():
    # Sends the request
    send(Command.LIST.value)

    # Gets the answer
    data = receive()

    # Convert to usable list (server list is made of single character strings)
    file_list = []
    i = 1
    # Word-wise loop
    while i < (len(data) - 2):
        string = ''
        # Character-wise loop
        while not (data[i] == ',' and data[i + 1] == ' '):
            if data[i] == '\'':
                if data[i + 1] == ']':
                    break
                i += 1
                continue
            string += data[i]
            i += 1
        i += 2
        file_list.append(string)
    return file_list


# Handles file listing request
def list_handler():
    file_list = get_file_list()

    # Prints the file list in a new frame
    list_frame = Frame(window, name='list')
    list_frame.pack()
    menu_frame.destroy()
    raise_frame(list_frame)
    Label(list_frame,
          text='All files in server:',
          font=Font(size=10)
          ).pack()
    list_box = ScrolledText(list_frame,
                            font=Font(family='Courier', size=10),
                            height=20)

    # Adds list items to box
    for index, item in enumerate(file_list):
        list_box.insert(END, file_list[index] + '\n')

    list_box.config(state=DISABLED)
    list_box.pack(fill='both', padx=WINDOW_WIDTH / 20)

    Button(list_frame,
           text='Back',
           font=Font(size=10),
           width=10,
           height=2,
           command=lambda: back(list_frame)
           ).pack()


# Handles get request
def get_handler():
    # Creates a new frame for the download
    download_frame = Frame(window, name='download')
    download_frame.pack()
    menu_frame.destroy()
    raise_frame(download_frame)
    Label(download_frame,
          text='Enter full file name or select a file:',
          font=Font(size=10)
          ).pack()
    file_name = StringVar()

    file_list = get_file_list()
    Combobox(download_frame,
             values=file_list,
             width=40,
             textvariable=file_name,
             justify='center',
             font=Font(size=10)
             ).pack()

    Button(download_frame,
           text='Download File',
           font=Font(size=10),
           width=15,
           height=2,
           command=lambda: get(file_name.get(), message_label)
           ).pack()

    message_label = Label(download_frame)
    message_label.pack()

    Button(download_frame,
           text='Back',
           font=Font(size=10),
           width=10,
           height=2,
           command=lambda: back(download_frame)
           ).pack()


# Handles put request
def put_handler():
    # Creates a new frame for the upload
    upload_frame = Frame(window, name='upload')
    upload_frame.pack()
    menu_frame.destroy()
    raise_frame(upload_frame)
    Label(upload_frame,
          text='Enter file path:',
          font=Font(size=10)
          ).pack()
    file_name = StringVar(upload_frame, value='')
    file_entry = Entry(upload_frame,
                       textvariable=file_name,
                       width=60,
                       justify='center',
                       font=Font(size=10))
    file_entry.pack()

    Button(upload_frame,
           text='Choose File',
           font=Font(size=10),
           width=15,
           height=2,
           command=lambda: file_name.set(filedialog.askopenfilename().replace('/', os.sep))
           ).pack()

    Button(upload_frame,
           text='Upload File',
           font=Font(size=10),
           width=15,
           height=2,
           command=lambda: put(file_entry.get(), message_label)
           ).pack()

    message_label = Label(upload_frame)
    message_label.pack()

    Button(upload_frame,
           text='Back',
           font=Font(size=10),
           width=10,
           height=2,
           command=lambda: back(upload_frame)
           ).pack()


# Creates menu frame
def create_menu_frame():
    menu = Frame(window, name='menu')
    menu.pack()

    # Adding buttons
    button_width = 30
    button_height = 4

    Button(menu,
           text='List all files',
           command=list_handler,
           width=button_width,
           height=button_height,
           font=Font(size=10)
           ).pack(pady=button_height)
    Button(menu,
           text='Upload file',
           command=put_handler,
           width=button_width,
           height=button_height,
           font=Font(size=10)
           ).pack(pady=button_height)
    Button(menu,
           text='Download file',
           command=get_handler,
           width=button_width,
           height=button_height,
           font=Font(size=10)
           ).pack(pady=button_height)

    raise_frame(menu)
    return menu


# Creating GUI
window = Tk()
WINDOW_WIDTH = int(window.winfo_screenwidth() / 2)
WINDOW_HEIGHT = int(window.winfo_screenheight() / 2)
window.geometry(str(WINDOW_WIDTH) + 'x' + str(WINDOW_HEIGHT))
window.protocol('WM_DELETE_WINDOW', on_close)
window.iconbitmap('colored_arrows.ico')

menu_frame = create_menu_frame()

# Execute window
window.mainloop()
