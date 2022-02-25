import os
import string
import random
import time

SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096
SIZE_BYTES = 4
SLEEP_TIME = 0.8


def get_os():
    """
    The function check if '/' is the sep in the path, like we use in linux.
    :return: 0 - windows, 1 - linux
    """
    return 1 if os.sep == '/' else 0


def get_sep(num):
    """
    The function return current os sep.
    :return: / - linux, \\ - windows
    """
    return '/' if num == 1 else '\\'


def wait_for_file(file_path):
    """
    The function try to open the received file.
    that's how we check that the os done to create the file.
    """
    while True:
        try:
            with open(file_path, "rb"):
                return True
        except:
            continue


def get_size(file_path):
    """
    The function try to open the received file.
    that's how we check that the os done to create the file.
    """
    previous = os.path.getsize(file_path)
    while True:
        time.sleep(0.3)
        cur = os.path.getsize(file_path)
        if cur == previous:
            return cur
        previous = cur


def fix_path(path: str, other_os):
    """
    The function get the path and the os that we want to run on.
    :return: the path on the current os.
    """
    # if the operating systems are the same do nothing.
    # else, replacing the other-sep with the cur-sep.
    if get_os() != other_os:
        path = path.replace(get_sep(other_os), os.sep)

    # getting abs path
    return os.path.abspath(os.path.expanduser(path))


class Database:
    """
    Class database, hold the action and commend of all users and pc.
    """

    def __init__(self) -> None:
        super().__init__()
        self.users = {}

    def add_user(self, user_id):
        """
        The function add user to the database.
        """
        if user_id in self.users.keys():
            raise Exception("user already exist")

        self.users[user_id] = {}

    def add_pc(self, user_id, pc_id):
        """
        The function add pc to user in the database.
        """
        if user_id not in self.users.keys():
            # user not exist
            exit(0)

        if pc_id in self.users[user_id]:
            # pc already exist
            return

        self.users[user_id][pc_id] = []

    def add_action(self, user_id, cur_pc_id, flag, data):
        """
        The function add action to all other pc of given user.
        """
        for pc in self.users[user_id]:
            if pc == cur_pc_id:
                continue

            self.users[user_id][pc].append((flag, data))

    def get_actions(self, user_id, pc_id):
        """
        :return: actions of given pc.
        """
        return self.users[user_id][pc_id]

    def clear_actions(self, user_id, pc_id):
        """
        The function deletes all action of given pc.
        """
        self.users[user_id][pc_id] = []


class MessageProtocol:
    """
    MessageProtocol class used to convert the action that we use to number in the protocol(like enum).
    """
    register = "1"
    login = "2"
    file_created = "3"
    file_modified = "4"
    moved = "5"
    file_deleted = "6"
    folder_created = "7"
    folder_deleted = "8"
    ping = "9"


def generate_id(size=128):
    """
    :return: the function return generated id of given size.
    """
    return ''.join(random.SystemRandom().choice(string.digits + string.ascii_letters) for _ in range(size))


def int_to_byte(num: int):
    """
    :return: convert int to byte.
    """
    return num.to_bytes(SIZE_BYTES, "big")


def byte_to_int(byte: bytes):
    """
    :return: convert byte to int.
    """
    return int.from_bytes(byte, "big")


def send_message(s, *parts):
    """
    The function connect all the part of the message and sent it.
    """
    message = parts[0]
    for part in parts[1:]:
        message += SEPARATOR + part

    message = message.encode("utf-8")
    s.sendall(int_to_byte(len(message)) + message)


def send_file(sock, file_path):
    """
    The function receive socket and path to file and send the file.
    """

    # Check that the file exist.
    if not os.path.exists(file_path):
        # file not exist to send
        exit(0)

    # open the file and send it.
    with open(file_path, "rb") as file:
        while True:
            bytes_read = file.read(BUFFER_SIZE)

            # done with file
            if not bytes_read:
                break

            sock.sendall(bytes_read)


def receive_file(sock, file_path, file_size):
    """
    The function receive socket, file and the size and get the file.
    """
    file_size = int(file_size)
    with open(file_path, "wb") as file:
        while True:
            buffer_size = min(BUFFER_SIZE, file_size)
            bytes_read = sock.recv(buffer_size)

            # done with file
            if file_size == 0:
                break

            file.write(bytes_read)
            file_size -= len(bytes_read)

    return file_path


def create_folder(path):
    """
    The function get path and create the folder.
    """

    # if the folder already exist return.
    if os.path.exists(path):
        return

    # create the new dir
    os.makedirs(path)


def delete_file(path):
    """
    The function get path and delete the file.
    """
    if not os.path.exists(path):
        return

    os.remove(path)


def delete_folder(path):
    """
    The function get path and delete the folder.
    """
    if not os.path.exists(path):
        return

    # run through the files and dirs
    for root, dirs, files in os.walk(path, topdown=False):

        # remove the files
        for file in files:
            os.remove(os.path.join(root, file))

        os.rmdir(root)


def move_file_folder(src: str, dest: str):
    """
    The function get path to source file/folder and destination and move the file/folder to there.
    """

    # if file not exist - do nothing
    if not os.path.exists(src):
        return

    # moving the file and folder
    os.renames(src, dest)
