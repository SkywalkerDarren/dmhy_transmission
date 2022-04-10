import csv
import json

import requests
from bs4 import BeautifulSoup
from transmission_rpc import Client

dmhy_url = 'https://dmhy.org/topics/rss/rss.xml'


def read_config():
    with open('config.json') as f:
        return json.load(f)


def read_downloaded_set():
    with open('DownloadedList.csv', encoding='utf-8') as f:
        csv_file = csv.DictReader(f)
        return {data['title'] for data in csv_file}


def read_search_list():
    with open('SearchList.csv', encoding='utf-8') as f:
        csv_file = csv.DictReader(f)
        return [data for data in csv_file]


def fetch_search_result(keywords, proxy):
    resp = requests.get(dmhy_url, params=[('keyword', keywords)], proxies=proxy)
    print(f"searched: {keywords}")
    return resp.content.decode('utf-8')


def find_magnet_link(xml_data, need_filter):
    soup = BeautifulSoup(xml_data, 'xml')
    return {item.title.contents[0]: item.enclosure.attrs['url'] for item in soup.find_all('item')
            if item.title.contents[0] not in need_filter}


def send_to_transmission(link_map, config):
    client = Client(protocol=config["protocol"],
                    host=config["host"],
                    port=config["port"],
                    path=config["path"],
                    username=config["username"],
                    password=config["password"],
                    timeout=config["timeout"])
    ver = client.rpc_version
    print(f"transmission rpc version: {ver}")
    success_map = {}
    for title, url in link_map.items():
        try:
            # client.add_torrent(url)
            print(f"file added: {title}")
            success_map[title] = url
        except Exception as e:
            print(f"file unadded: {title} err: {e}")
    return success_map


def log_link_downloaded(downloaded_map: map):
    with open('DownloadedList.csv', 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        rows = [[title, url] for title, url in downloaded_map.items()]
        writer.writerows(rows)


def run():
    config = read_config()
    need_filter = read_downloaded_set()
    data = read_search_list()

    download_map = {}
    for search in data:
        xml_data = fetch_search_result(search['keywords'], config['proxy'])
        link_map = find_magnet_link(xml_data, need_filter)
        download_map.update(link_map)

    downloaded_map = send_to_transmission(download_map, config['transmission'])
    log_link_downloaded(downloaded_map)


if __name__ == '__main__':
    run()
