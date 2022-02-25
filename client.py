import socket
import sys
import time

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

from utils import *

server_ip = sys.argv[1]
server_port = int(sys.argv[2])
path_to_monitor = sys.argv[3]
sync_timer = float(sys.argv[4])

user_id = None
if len(sys.argv) == 6:
    user_id = sys.argv[5]

pc_id = str(get_os()) + generate_id(127)
file_currently_downloading = None


def sync(sock):
    """
    The function received message and act as told.
    """

    # send to the server the ping request
    send_message(sock, MessageProtocol.ping, user_id, pc_id, '')

    while True:
        # receive the header size
        message = sock.recv(SIZE_BYTES)

        # if there is no data close the connection
        if not message:
            break

        # receive the message and create the file/folder
        size = byte_to_int(message)
        message = sock.recv(size).decode("utf-8")
        flag, data = message.split(SEPARATOR, 1)

        if flag == MessageProtocol.file_created:
            file_path, file_size = data.split(SEPARATOR, 1)

            # flag that the file is being downloaded
            global file_currently_downloading
            file_path = os.path.normpath(file_path)
            file_currently_downloading = path_to_monitor + file_path

            receive_file(sock, file_currently_downloading, file_size)

            time.sleep(SLEEP_TIME)
            # check if no file is being downloaded
            file_currently_downloading = None

        # get the path in current os.
        data = os.path.normpath(data)
        file_path = path_to_monitor + data

        if flag == MessageProtocol.folder_created:
            # create the folder
            create_folder(file_path)

        if flag == MessageProtocol.folder_deleted or flag == MessageProtocol.file_deleted:

            # delete the file/folder
            if os.path.isdir(file_path):
                delete_folder(file_path)

            if os.path.isfile(file_path):
                delete_file(file_path)

        if flag == MessageProtocol.moved:
            # move the file/folder
            src, dest = data.split(SEPARATOR)
            src = path_to_monitor + src
            dest = path_to_monitor + dest
            move_file_folder(src, dest)


def send_start_folder():
    # going through the files and folder
    for root, dirs, files in os.walk(path_to_monitor, topdown=True):
        relative_root = create_relative_path(root)

        # sending folders
        for cur_dir in dirs:
            sock = create_connection()
            file_path = relative_root + os.sep + cur_dir
            send_message(sock, MessageProtocol.folder_created, user_id, pc_id, file_path)
            close_connection(sock)

        # sending files
        for file in files:
            sock = create_connection()

            file_path = root + os.sep + file
            relative_file_path = relative_root + os.sep + file

            # wait_for_file(file_path)
            # file_size = os.path.getsize(file_path)
            file_size = get_size(file_path)
            send_message(sock, MessageProtocol.file_created, user_id, pc_id, relative_file_path.removeprefix('.'),
                         str(file_size))
            send_file(sock, file_path)

            close_connection(sock)


def create_connection():
    """
    The function create socket and start connection.
    :return: new socket.
    """
    sock = socket.socket()
    sock.connect((server_ip, server_port))
    return sock


def close_connection(sock):
    """
    close the connection of the received socket.
    """
    sock.close()


def create_relative_path(relative_path: str):
    """
    The function receive path and return the relative to this path.
    """

    # removing from path
    return relative_path.replace(path_to_monitor, "", 1)


def on_created(event):
    """
    When on create event trigger the function create socket and send the update to the server.
    """

    # check if the event is the file that we are now downloading.
    if event.src_path == file_currently_downloading:
        return

    # create the connection to the server.
    s = create_connection()

    # check if file is created, if not event.is_directory.
    if os.path.isfile(event.src_path):
        file_path = create_relative_path(event.src_path)

        if not os.path.exists(event.src_path):
            close_connection(s)
            return

        # waiting for the os for finishing writing the file
        file_size = get_size(event.src_path)
        # file_size = os.path.getsize(event.src_path)
        send_message(s, MessageProtocol.file_created, user_id, pc_id, file_path, str(file_size))

        send_file(s, event.src_path)

    # check if dir is created, if event.is_directory.
    if os.path.isdir(event.src_path):
        send_message(s, MessageProtocol.folder_created, user_id, pc_id, create_relative_path(event.src_path))

    # close the connection.
    close_connection(s)


def on_modified(event):
    """
    When on modified event trigger the function create socket and send the update to the server.
    """

    # check if the event is the file that we are now downloading.
    if event.src_path == file_currently_downloading:
        return

    # check if the event is a dir if so pass
    if event.is_directory:
        return

    # update the file
    on_created(event)


def on_moved(event):
    """
    When on moved event trigger the function create socket and send the update to the server.
    """

    # check if the event is the file that we are now downloading.
    if event.src_path == file_currently_downloading:
        return

    s = create_connection()
    send_message(s, MessageProtocol.moved, user_id, pc_id, create_relative_path(event.src_path),
                 create_relative_path(event.dest_path))
    close_connection(s)


def on_deleted(event):
    """
    When on delete event trigger the function create socket and send the update to the server.
    """

    # check if the event is the file that we are now downloading.
    if event.src_path == file_currently_downloading:
        return

    s = create_connection()
    if not event.is_directory:
        send_message(s, MessageProtocol.file_deleted, user_id, pc_id, create_relative_path(event.src_path))

    if event.is_directory:
        send_message(s, MessageProtocol.folder_deleted, user_id, pc_id, create_relative_path(event.src_path))

    close_connection(s)


def register(sock):
    """
    Send a register request to the server.
    """
    send_message(sock, MessageProtocol.register, '', pc_id, '')
    global user_id
    user_id = sock.recv(BUFFER_SIZE).decode()
    send_start_folder()


def login(sock):
    """
    Send to the server the login request
    """
    send_message(sock, MessageProtocol.login, user_id, pc_id, '')

    while True:
        # receive the header size
        message = sock.recv(SIZE_BYTES)

        # if there is no data close the connection
        if not message:
            break

        # decode the message
        size = byte_to_int(message)
        message = sock.recv(size).decode("utf-8")
        flag, data = message.split(SEPARATOR, 1)

        # create the file/folder
        if flag == MessageProtocol.file_created:
            file_path, file_size = data.split(SEPARATOR, 1)
            file_path = os.path.normpath(file_path)
            receive_file(sock, path_to_monitor + file_path, file_size)

        if flag == MessageProtocol.folder_created:
            data = os.path.normpath(data)
            create_folder(path_to_monitor + data)


def turn_on():
    """
    The function turn on the watchdog to monitor the folder.
    """
    # making the dir to monitor
    os.makedirs(path_to_monitor, exist_ok=True)

    # first connection
    s = create_connection()
    if user_id is None:
        register(s)
    else:
        login(s)
    close_connection(s)

    # creating observer
    file_handler = PatternMatchingEventHandler(["*"], None, False, True)
    file_handler.on_created = on_created
    file_handler.on_deleted = on_deleted
    file_handler.on_modified = on_modified
    file_handler.on_moved = on_moved

    observer = Observer()
    observer.schedule(file_handler, path_to_monitor, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(sync_timer)

            # asking for sync
            s = create_connection()
            sync(s)
            close_connection(s)

    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def main():
    turn_on()


if __name__ == '__main__':
    main()
