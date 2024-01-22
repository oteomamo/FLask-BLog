# Flask Blog Oteo Mamo

## Description

This Python web application displays news from the Hacker News portal and allows all its users to interact with the posts and website by liking or disliking them. The project features pages for Sign Up/Login, News Feed, and Profile. For authorized users, it includes special admin features. All news items include a like and a dislike button. All registered users are allowed to create new posts, and they can also edit their name or nickname after registration. Users can also view all their posts and liked posts on their Settings Page. Auth0 is used for authentication in this project.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Configs](#configs)
- [Testing](#testing)

## Features

### Auth0 for Authentication
- All new users are assigned the role of 'User' through Auth0.
- Admin users can change the roles of other users in the database.

### User Posts
- All users can create new posts.

### User Profile Management
- Users can edit their Name and Nickname at [Settings Page](https://cop4521.oteomamo.com/settings).

### User Interactions
- Logged-in users can like or dislike and interact with all posts.
- Users can view their own posts and their likes/dislikes on the [Settings Page](https://cop4521.oteomamo.com/settings).

### Admin Privileges
- Admin users can view all user posts.
- Admin users can delete any post, which also removes all associated likes and dislikes.

### News Feed Updates
- The platform updates all posts every hour to display the most recent 30 news items.
- The most recent 30 news posts can also be viewed as a JSON file at [Newsfeed JSON](https://cop4521.oteomamo.com/newsfeed).



## Installation

### Prerequisites
- Server with Ubuntu 22.04 or similar Linux-based OS.
- Command line access on the server.
- Root or sudo privileges.

### Step 1: Clone Repository from GitLab
1. **Install Git** (if not already installed):
```
sudo apt-get update
sudo apt-get install git
```

2. **Clone the repository** to your server. Choose either SSH or HTTPS method:
- For SSH:
  ```
  git clone git@gitlab.com:cop45213741843/Flask_Blog.git
  ```
- For HTTPS:
  ```
  git clone https://gitlab.com/cop45213741843/Flask_Blog.git
  ```

### Step 2: Set Up Environment
1. **Install Python and pip** (if not already installed):
```
sudo apt-get install python3 python3-pip
```

2. **Install necessary libraries** using `requirements.txt`:
```
cd path/to/your/project
pip install -r requirements.txt
```

3. **Verify installation** for each package (example for Flask):
```
python -c "import flask; print(flask.__version__)"
```

### Step 3: Set Up Gunicorn
1. **Run the application** with Gunicorn (adjust the number of workers as necessary):
```
gunicorn -w 4 run:app
```

### Step 4: Set Up Nginx
1. **Install Nginx** (if not installed via `requirements.txt`):
```
sudo apt-get install nginx
```

2. **Configure Nginx** to proxy requests to Gunicorn. (Configuration details in the next section).
3. **Test Nginx configuration** for syntax errors:
```
sudo nginx -t
```

4. **Restart Nginx** to apply changes:
```
sudo systemctl restart nginx
```

### Step 5: Secure the Application
- **Set up SSL** with Let's Encrypt for HTTPS (e.g., using Certbot).
- **Configure firewalls** and other security measures as needed.


## Configs
All the necessary configuration files (Nginx, supervisor, Gunicorn, Cron etc) you need to setup your server and web application. Please exclude any kind of personal information. 

### Firewall Configuration
- Allow access to the following ports in your machine's firewall:

```
5000                       ALLOW       Anywhere
Nginx Full                 ALLOW       Anywhere
8000/tcp                   ALLOW       Anywhere
5000 (v6)                  ALLOW       Anywhere (v6)
Nginx Full (v6)            ALLOW       Anywhere (v6)
8000/tcp (v6)              ALLOW       Anywhere (v6)
443                        ALLOW OUT   Anywhere
3000                       ALLOW OUT   Anywhere
443 (v6)                   ALLOW OUT   Anywhere (v6)
3000 (v6)                  ALLOW OUT   Anywhere (v6)
```
### Nginx configuration
- Run the following command to edit the Nginx configuration file:
```
sudo nano /etc/nginx/sites-enabled/cop4521.oteomamo.com
```

- Use the following configuration settings:
```
server {
    server_name cop4521.oteomamo.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-M>
        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range';
        include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
        add_header Public-Key-Pins 'pin-sha256="base64+primary+key"; pin-sha256="base64+backup+key"; max-age=2592000; includeSubDomains';


    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/cop4521.oteomamo.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cop4521.oteomamo.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

server {
    if ($host = cop4521.oteomamo.com) {
        return 301 https://$host$request_uri;
    }

    listen 80;
    server_name cop4521.oteomamo.com;
    return 404; # managed by Certbot
}
```
### Cron Job Configuration

- The cron job configuration should be set outside the project directory or adjusted accordingly if placed inside the directory.
- The script manage_server.sh should look like:
```
#!/bin/bash

export PATH=$PATH:/home/oteo/.local/bin/

# Go to Flask_Blog directory
cd ~/Flask_Blog

# Kill the running gunicorn process
pkill gunicorn

# Set Flask app environment variable
export FLASK_APP=run.py
sleep 2
RANDOM_NUM=$(printf "%08d" $((RANDOM+10000000)))
# Initialize, migrate, and upgrade the database
flask db init
sleep 2
flask db migrate -m "Upgrade$RANDOM_NUM"
sleep 2
flask db upgrade 

# Start the Flask app using gunicorn in the background
gunicorn -w 4 run:app &
```

- Set up the cron job as follows:
1. Open the crontab configuration:
```
crontab -e
```
2. Add the following line to execute the script every hour:
```
0 * * * * /home/user/manage_server.sh >> /home/user/dbfinal.log 2>&1
```

3. Schedule the database update cron job (using update_news.py):
```
0 * * * * /usr/bin/python3 /home/user/Flask_Blog/update_news.py >> /home/user/Flask_Blo>
```
- Replace /home/user with your actual user directory.

## Testing


### To test the files using Pylint, execute the following commands:

- First, install Pylint:
```
pip install pylint
```
- Then run it on the porject directory or individual files
```
pylint Flask_Blog/
```

- The Flask_Blog directory above does not include Migrations of the database as they are generated automaticly when you run the manage_server.sh script 

### To test the funcionality of the code itself you can use Pytest

- First, install Pylint:
```
pip install pytest
```
- Then run it on the porject directory or individual files
```
cd Flask_Blog
pylint
```

- The above test will run for teh test_sample.py file inside the test directory which tests two of the main functions of the application the home route and the update_interactions function that determines if a user has liked, disliked a post oor not interacted with it at all. To test other parts of the project you can write similar functions custem to teh new code in the same file. 

### To test the front end side of the application and security visit
```
https://observatory.mozilla.org/analyze/cop4521.oteomamo.com
```


### To test the server security 
```
sudo lynis audit system
```
