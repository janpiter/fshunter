##### Please be aware that automated crawling of these websites violates their Terms of Service. This is for educational purposes only!

# Flash Sale Hunter
Flash Sale Crawler for Indonesia Marketplace.

## Installation
1. Import `config.json` file under **data** directory into MongoDB:
    ```
    $ mongoimport --host <YOUR_MONGODB_HOST> --port <YOUR_MONGODB_PORT> --db <YOUR_DATABASE_NAME> --collection <YOUR_COLLECTION_NAME> --file data/config.json 
    ```
    (Read more about [importing data in MongoDB](https://docs.mongodb.com/manual/reference/program/mongoimport "MongoDB Help")).
2. Install required libraries using pip:
    ```
    $ pip install -r requirements.txt
    ```

3. Setup `config.ini` file:
    ```
    [mongodb]
    host = <YOUR_MONGODB_HOST>
    port = <YOUR_MONGODB_PORT>
    database = <YOUR_DATABASE_NAME>
    collection = <YOUR_COLLECTION_NAME>
    
    [sentry]
    host = <YOUR_SENTRY_CLIENT_KEY>
    
    ; The section below is only an option, for further data processing only.
    [nsq]
    host = <YOUR_NSQ_HOST>
    tcp_port = <YOUR_NSQ_TCP_PORT>
    http_port = <YOUR_NSQ_HTTP_PORT>
    topic_items = <YOUR_NSQ_TOPIC_NAME>
    ```
    (Read more about [Sentry](https://docs.sentry.io "Sentry Documentation") and [NSQ](https://nsq.io "NSQ - A realtime distributed messaging platform")).
    
## Usage
```
usage: crawl.py [-h] [--output {csv,json,xls,xlsx}] [--file_path FILE_PATH]
                [--file_name FILE_NAME] [--publish {True,False}]
                [--debug {True,False}]
                marketplace

Marketplace flash sale crawler

positional arguments:
  marketplace           Marketplace name (shopee, bukalapak, tokopedia, jd.id,
                        elevenia)

optional arguments:
  -h, --help            show this help message and exit
  --output {csv,json,xls,xlsx}
                        Type of file for output (csv, json, xls, xlsx)
  --file_path FILE_PATH
                        Output file path (default: /tmp)
  --file_name FILE_NAME
                        Output file name (default: Y.m.d.H-marketplace_name)
  --publish {True,False}
                        Publish data to NSQ
  --debug {True,False}
```

#### Example usage:
```
$ python2.7 -m fshunter.apps.crawl elevenia --output csv --file_path ~/Desktop
```
