##### Please be aware that automated crawling of these websites violates their Terms of Service. This is for educational purposes only!

# Flash Sale Hunter
Flash Sale Crawler for Indonesia Marketplace.

## Installation
1. Import `config.json` file under **data** directory into mongodb:
    ```
    $ mongoimport --db <YOUR_DATABASE_NAME> --collection <YOUR_COLLECTION_NAME> --file data/config.json 
    ```
    (<a href="https://docs.mongodb.com/manual/reference/program/mongoimport" target="_blank">Read more about importing data in mongodb</a>).

2. Install required libraries using pip:
    ```
    $ pip install -r requirements.txt
    ```

3. Setup `config.conf` file:
    ```
    [mongodb]
    host = <YOUR_MONGODB_HOST>
    port = <YOUR_MONGODB_PORT>
    database = <YOUR_DATABASE_NAME>
    collection = <YOUR_COLLECTION_NAME>
    ```
 
## Usage
```
usage: crawl.py [-h] --marketplace {shopee,bukalapak}
                [--output {csv,json,xls,xlsx}] [--file_path FILE_PATH]
                [--file_name FILE_NAME]

Marketplace flash sale crawler.

optional arguments:
  -h, --help            show this help message and exit
  --marketplace {shopee,bukalapak}
                        Marketplace name.
  --output {csv,json,xls,xlsx}
                        Type of file for output (csv, json, xls, xlsx).
  --file_path FILE_PATH
                        File path (default: /tmp).
  --file_name FILE_NAME
                        File name (default: marketplace name).
```

#### Example usage:
```
$ python2.7 -m fshunter.apps.crawl --marketplace bukalapak --output xlsx --file_path ~/Desktop/ --file_name "Flash-sale-BL"
```
