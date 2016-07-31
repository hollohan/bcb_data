
# Setup on dietpi
### prereq
install mysql:
`apt-get install mysql-server-5.5`
        - prompted for root password during setup
create DB with tables explained in 'poloDBschames'
 
install git:
`apt-get install git`

install python 2.7:
`apt-get install python2.7`

install pip:
`apt-get install python-pip`

install python c headers:
`apt-get install python2.7-dev`

install twisted:
`pip install twisted`

install autobahn:
`pip install autobahn`

install pymysql:
`pip install pymysql`

install service_identity:
`pip install service_identity`

install flask:
`pip install flask`

install tornado:
`pip install tornado`

install screen:
`apt-get install screen`

install plotly
`pip install plotly`

### clone github repo

`git clone https://github.com/hollohan/bot`


### config
requires file ../creds which contains:
{
"api_key",
"api_secret",
"login",
"passwd",
"crt_file",
"key_file"
}

### crt_file/key_file
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout server.key -out server.crt
