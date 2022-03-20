# Cloud-Service
Implementation of a cloud backup system. 
The project includes client and server-side program, the client monitors a chosen folder for changes, and back up its content to a server running the server-side program which manages the backup system. 
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
for example `python3 client.py 1.2.3.4 12345 backup_folder 10`
with this configuration it will backup to the server in (1.2.3.4, 12345), the folder to backup is `backup_folder` (relative to the code) and will sync every 10 sec. 
