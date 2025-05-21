# Sensor Management System



## Initial Setup

#### Required software:
- screen (preinstalled on Ubuntu)
- openssl (preinstalled on Ubuntu)
- python 3.11
- sudo apt install python3.11-venv
- sudo apt install certbot python3-certbot-nginx

#### Install the Application:

1. Clone the repository

2. In the root directory, create a virtual environment to install the dependencies:

   $ `python3.11 -m venv env`

3.  Activate the virtual environment:

   $ `source env/bin/activate`

4. Install the requirements:

   (env)$ `pip install -r requirements.txt`

5. Create the jwt-secrets file:

   (env)$ `echo 'AUTHJWT_SECRET_KEY="placeMySecretKeyHere"' > env/.env`

6. Deactivate the virtual environment by entering `deactivate`

Note: if a system upgrade messes with the virtual environment and upgrades python version by accident, the simplest fix is to uninstall the virtual environment (`rm -r env`), install python3.11 if it's not on the system anymore and create a new virtual environment (step 2 to 6).

#### Install MongoDB on Ubuntu 20.04:

1. Import the public key used by the package management system:

   $ `wget -qO - https://www.mongodb.org/static/pgp/server-5.0.asc | sudo apt-key add -`

2. Create a list file for MongoDB:

   $ `echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list`

3. Reload the package database:

   $ `sudo apt-get update`

4. Install MongoDB packages:

   $ `sudo apt-get install -y mongodb-org`

#### Install and Setup Nginx:

1. Install Nginx:

   $ `sudo apt update && sudo apt install nginx`

2. Move `http.conf` to `/etc/nginx/conf.d/` and edit its root and index to point to the correct locations

3. In `nginx.conf` comment out or delete the line `include /etc/nginx/sites-enabled/*;`

4. Reload Nginx:

   $ `sudo nginx -s reload`

#### LetsEncrypt Certbot setup:

1. $ `sudo apt install certbot python3-certbot-nginx`

2. Modify the `http.conf` in `/etc/nginx/conf.d/`: 
   1. Remove all parts that are handeled by Certbot (the lines with comments).
   2. Change the `listen 443 ssl http2;` to `listen 80;`

3. Reload NginX: $ `sudo systemctl reload nginx`

4. Run Certbot to create the certificates: $ `sudo certbot --nginx -d discosat.cs.uni-kl.de`

5. Start the Certbot Timer: $ `sudo systemctl start certbot.timer`

   

## Run the Application

Use the `startup.sh`-script or do it manually:

1. Start nginx:

   $ `sudo service nginx start/stop/status` or do $ `sudo nginx -s reload` for reloading

2. Start the Certbot Timer: $ `sudo systemctl start certbot.timer`

3. Start mongoDB:

   $ `sudo service mongod start/stop/status`

4. The application has to be run in the virtual environment where the requirements are installed.

   $ `cd discosat_server`

​   $ `source env/bin/activate`

​   Note: The virtual environment can be deactivated by entering `deactivate`

Furthermore, set PYTHONPATH as the current directory:

​   (env)$ `export PYTHONPATH=$PWD`

Finally, run the application:

​   (env)$ `python3 app/main.py`


## Run the Application using screen
1. `screen` :open a screen session

2. `./startup.sh`

3. `strg+a`, `d` :detatch the current session

4. `screen -ls` :list all detatched sessions

5. `screen -r <sessionName>` :connect to a specific session


## Development environment

Do not run the development environment on the live-server!

The development environment offers: 

- FastAPI development-page (127.0.0.1:8000/docs)

#### To activate the dev-environment:
   
1. Delete the http.conf: $ `rm http.conf`

2. Copy http_dev.conf to http.conf: $ `cp http_dev.conf http.conf` 

3. http.conf: change `root /home/disco/discosat_server/app/static;` to your own path to the /app/static-folder

4. Copy the http.conf to `/etc/nginx/conf.d/http.conf`

5. Modify `startup.sh`: comment out the block about the certbot-timer

6. Run `startup.sh`

7. Open website via `http://127.0.0.1` or FastAPI via `127.0.0.1:8000/docs`

8. Modify the mongoDB as shown below to create a inital dummy-account.

Differences between dev-env and live-env:

1. http.conf: removed `|docs/` from line `location ~ ^/(data/|fixedjobs/|docs/|sensors/|login/)`

2. http.conf: modified line `proxy_pass http://0.0.0.0:8000;` to `proxy_pass http://127.0.0.1:8000;`

3. Added https and a http-reroute to the http.conf.


#### Setup the database:
IMPORTANT: make sure to only use the insecureAdminLogin (dummy account) in development environment. Create a real admin account by using this dummy account, than delete this dummy.

1. Start the dev-env as descried above.

2. Open the virtual envoronment: 

   $ `source env/bin/activate`

3. Open mondodb-shell: 

   $ `mongo` (or depending on the system: $ `mongosh`)

4. Check that the database "sensors" is available: 

   $ `show dbs`

5. Change to the sensors database or create it if non-existent yet (is the same command): 

   $ `use sensors`

6. Insert dummy user "insecureAdminLogin" and implicitly create the collection "users":

   $ `db.users.insert({ "_id" : ObjectId("6431594b33bd9273ce33f0b2"), "email" : "test@mail.com", "username" : "insecureAdminLogin", "hashed_password" : BinData(0,"JDJiJDEyJGdmWllwN0NoYmNjdlJyTmhkakJPcXU2VEVNMVpYamtWVUptRnVpYkNnZGc0UUZNVjBwdVVX"), "role" : "admin", "creation_date" : 954587471, "owned_sensors" : [ ], "scheduled_jobs" : [ ], "online_status" : [ [ 0, 0 ] ], "public_rsa_key" : "" })`

6. Verify that the collection "users" is available: 

   $ `show collections`

7. Show all registered users: 

   $ `db.users.find()`

#### Dummy admin account
On live systems NEVER use the insecureAdminLogin!

User: insecureAdminLogin
Password: insecurePasswordRemoveAfterAdminCreated123onZhs2LipBPZVg2itHJsoS7U5tkywsxP


## TODOs

- [X] Webinterface.UserDetails: Implement missing buttons for user account management.
- [ ] Webinterface.FixedJobs: show local-time and convert to timestamp when creating a new job. Add some buttons [+1 min, +10 min, +1h] for simple interaction.
- [ ] Webinterface.FixedJobs: method 'get_fixed_jobs_by_sensorname' rename the router-path from "/fixedjobs/{name}" to "/fixedjobs/sensor_name/{name}" for clarification. But this also needs to be adjusted in the sensors!
- [X] Webinterface.SensorDetails: add "are you sure" window, before the new JWT for a new sensor is created (otherwise you can remove sensors from the server with this accedentally). (TODO: in progress (to test)
- [ ] Webinterface.FixedJobs: when creating new fixed job, ensure not required arguments are not enforced (ensure every command has default parameters)
- [ ] Webinterface.FixedJobs: when creating new fixed job, make it possible to select sensor directly
- [X] Public website: make the connection to osm secure, so that it does not rise a tls-warning
- [ ] Webinterface.Data: add possiblity to filter/sort data collection
- [ ] Webinterface.Data: add upload-time to data-table

## Troubleshooting

This section lists errors that can occur by wrongly operating the application and how to fix them.

- Getting `localhost:27017: [Errno 111] Connection refused` when trying to call the API (for example by loading the webpage):

  The MongoDB service `mongod` wasn't shut down properly with $ `sudo service mongod stop` and the lock file still exists, not allowing the service to launch. Remove the lock file and start the service:

  ​	$ `sudo rm /var/lib/mongodb/mongod.lock`
  ​	$ `sudo service mongod start`

- MongoDB-shell: 

   $ `mongo` (Ctrl+c for exit)

- Create Certficates: $ `openssl req -x509 -newkey rsa:4096 -sha256 -days 365 -nodes -keyout discosat.cs.uni-kl.de.key -out discosat.cs.uni-kl.de.crt -subj "/C=DE/ST=Rhineland-Palatinate/L=Kaiserslautern/O=University Kauserslautern/OU=DistributedComputerSystemsLab/CN=www.discosat.cs.uni-kl.de" -addext "subjectAltName=DNS:discosat.cs.uni-kl.de,DNS:www.discosat.cs.uni-kl.de,DNS:discosat.informatik.uni-kl.de,DNS:www.discosat.informatik.uni-kl.de"`

- "I set up ngnix correctly but get a 404." -> check if the http user can access the discosat directory. This is can be a problem in development settings. 
  Test access: `sudo -u http stat <path>/discosat`

#### Delete a user and his tokens directly in the DB

1. Open the virtual envoronment: $ `source env/bin/activate`

2. Open mondodb-shell: $ `mongo`

3. Check that the target user is available: $ `db.users.find({"username":"insecureAdminLogin"})` or `db.users.find({"email":"testmail@test.com"})`

4. Delete the user: $ `db.users.deleteOne({"username":"insecureAdminLogin"})` or delete all with one mail adress `db.users.deleteMany({"email":"testmail@test.com"})`

5. Find the refresh-token: $ `db.refresh_token_whitelist.find({"sub":"insecureAdminLogin"})`

6. Remember the "sibling_jti", this is the JSON Web Token ID of the corresponding access-token. 

7. Delete the refresh-token: $ `db.refresh_token_whitelist.deleteOne({"sub":"insecureAdminLogin"})` or using the jti `db.refresh_token_whitelist.deleteOne({"jti":"INSERT-YOUR-JTI-HERE"})`

8. Add the access-token to the black list: `db.access_token_blacklist.insertOne({"jti" : "INSERT-SIBLING-JTI-HERE", "sub" : "INSERT-SUBJECT-NAME-HERE", "expire" : "INSERT-EXPIRATION-DATE-HERE", "time_added" : "INSERT-CURRENT-DATE-HERE"})`. Use an expiration date of today+3 days (make sure it is blocked long enough). The dates must be in format "YYYY-mm-dd HH:MM:SS", example "2020-12-31 23:59:59". 

## Bugs

- Webinterface.FixedJobs: deleting a fixed job does not remove the job from the sensors joblist

- When a job-file is uploaded, the DB entry is created before the file is stored on the disk. If a soring-error occures, there is no file on the disk, but an entry in the DB.

- ...







