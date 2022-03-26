# Cloud-Service
Implementation of a cloud backup system.  
The project includes client and server-side program, the client monitors a chosen folder for changes, and backs up it's content to a server.  
The server is running the server-side program which manages users and the backup system.  
The file is transferred over TCP and uses a custom communication protocol.  
This project is part of Introduction to communication course.  

### Features
- Monitor for changes in folder and sub-folder such as create, delete, and modify a file and folder. 
- Supports multiple users, each can have multiple computers. 
- Sync between user’s multiple computers. 
- Support in windows and Linux. 

## How To Run
The program uses third party library [Watchdog](https://github.com/gorakhargosh/watchdog).

#### run server
Server side receive the port to bind to.
for example `python3 servery.py 12345`

#### run client
Client side receive the ip and port of the server, the path to the folder, and sync time  
for example `python3 client.py 1.1.1.1 11111 backup_folder 10`  
with this configuration it will backup the folder at path `backup_folder` (relative to the code) to the server in ip=1.1.1.1 port=11111, and will sync every 10 sec. 
