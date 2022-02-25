import socket
import sys

from utils import *

server_ip = "127.0.0.1"
server_port = int(sys.argv[1])

database = Database()
NUMBER_OF_SOCKETS = 10


def path_for_user(user_id, path):
    """
    The function received user id and path and return the user path.
    """

    # creating path relative to server
    return "." + os.sep + user_id + path


def send_user_data(sock, user_id, other_os):
    """
    The function walk through all the folder and file of the client and send them.
    """

    # creating the path
    user_root = "." + os.sep + user_id

    # if user not exist
    if not os.path.exists(user_root):
        # file exist on create user - logical error
        exit(0)

    # going through the files and folder
    for root, dirs, files in os.walk(user_root, topdown=True):
        # sending folders
        for cur_dir in dirs:
            other_sep = get_sep(other_os)
            root_without_user_id = root.replace(user_id, '', 1)
            client_file_path = root_without_user_id.replace(os.sep, other_sep) + other_sep + cur_dir
            send_message(sock, MessageProtocol.folder_created, client_file_path.removeprefix('.'))

        # sending files
        for file in files:
            # creating the client path to file
            other_sep = get_sep(other_os)
            root_without_user_id = root.replace(user_id, '', 1)
            client_file_path = root_without_user_id.replace(os.sep, other_sep) + other_sep + file

            # creating the server path to file
            server_file_path = root + os.sep + file

            file_size = os.path.getsize(server_file_path)
            send_message(sock, MessageProtocol.file_created, client_file_path.removeprefix('.'), str(file_size))
            send_file(sock, server_file_path)


def create_user(sock, pc_id):
    """
    The function receive user id, generate user pc and add it to the database.
    """

    # generating id
    user_id = generate_id()
    print(user_id)

    # add the new user to the users map
    database.add_user(user_id)
    database.add_pc(user_id, pc_id)

    # creating the empty folder
    try:
        os.makedirs(user_id)
    except FileExistsError:
        # file exist on create user - logical error
        exit(0)

    # send for the client the new id
    sock.sendall(user_id.encode())


def sync(sock, user_id, pc_id):
    """
    The function check if the user has updates, if so send him all the action that he need to do.
    """

    # if there is nothing to do
    if not database.get_actions(user_id, pc_id):
        return

    for action in database.get_actions(user_id, pc_id):
        # extracting command data and other side os
        flag, data = action
        other_os = int(pc_id[0])

        if flag == MessageProtocol.file_created:
            # creating server side path to file to send
            file_path = path_for_user(user_id, data)

            if not os.path.exists(file_path):
                continue

            # getting the file size and preparing file path to send
            file_size = os.path.getsize(file_path)
            data = data.replace(os.sep, get_sep(other_os))

            # sending header message and file
            send_message(sock, flag, data, str(file_size))
            send_file(sock, file_path)

        else:
            # preparing file path to send and sending command message
            data = data.replace(os.sep, get_sep(other_os))
            send_message(sock, flag, data)

    # cleaning pc tasks from db
    database.clear_actions(user_id, pc_id)


def receive_message(sock):
    """
    Receive the message from the client and do as he request.
    """
    # extracting the message size and getting the message
    size = byte_to_int(sock.recv(SIZE_BYTES))
    message = sock.recv(size).decode("utf-8")

    if not message:
        return

    # extracting all the info
    flag, user_id, pc_id, data = message.split(SEPARATOR, 3)
    other_os = int(pc_id[0])

    if flag == MessageProtocol.register:
        # creating user
        create_user(sock, pc_id)
        sock.close()
        return

    if flag == MessageProtocol.login:
        # adding pc to user
        database.add_pc(user_id, pc_id)

        # sending current file to pc
        send_user_data(sock, user_id, other_os)
        sock.close()
        return

    if flag == MessageProtocol.ping:
        # starting sync
        sync(sock, user_id, pc_id)
        sock.close()
        return

    if flag == MessageProtocol.file_created:
        # extracting path and size from data
        file_path, file_size = data.split(SEPARATOR, 1)

        # fixing path to the server point of view
        file_path = file_path.replace(get_sep(other_os), os.sep)

        # adding action to database
        database.add_action(user_id, pc_id, flag, file_path)

        file_path = path_for_user(user_id, file_path)

        # create the base folder
        create_folder(os.path.dirname(file_path))

        # open the file and get the rest of the data from the client
        receive_file(sock, file_path, file_size)

        # closing connection
        sock.close()
        return

    data = os.path.normpath(data)
    data = data.replace(get_sep(other_os), os.sep)

    if flag == MessageProtocol.folder_created:
        create_folder(path_for_user(user_id, data))

    if flag == MessageProtocol.moved:
        # extracting src and dest from data and fixing them to server side path
        src, dest = data.split(SEPARATOR)
        src = path_for_user(user_id, src)
        dest = path_for_user(user_id, dest)
        move_file_folder(src, dest)

    if flag == MessageProtocol.folder_deleted or flag == MessageProtocol.file_deleted:
        # fixing the path
        file_path = path_for_user(user_id, data)

        # check if what to delete is a file or a folder
        if os.path.isdir(file_path):
            delete_folder(file_path)

        if os.path.isfile(file_path):
            delete_file(file_path)

    # fixing data to server side os and adding the data to db
    data = data.replace(get_sep(other_os), os.sep)
    database.add_action(user_id, pc_id, flag, data)
    sock.close()
    return


def turn_on():
    """
    The function turn on the server.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_ip, server_port))
    server.listen(NUMBER_OF_SOCKETS)

    while True:
        client_socket, client_address = server.accept()
        receive_message(client_socket)


def main():
    turn_on()


if __name__ == '__main__':
    main()
