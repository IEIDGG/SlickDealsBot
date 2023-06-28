from bs4 import BeautifulSoup
import requests
import time
from datetime import datetime
import pytz
import html
import urllib.parse


def extract_variable_definitions(file_path):
    variable_definitions = {}

    with open(file_path, 'r') as file:
        lines = file.readlines()

        for line in lines:
            line = line.strip()

            if line.startswith('var '):
                parts = line.split('=')
                if len(parts) >= 2:
                    variable_name = parts[0].replace('var ', '').strip()
                    variable_value = '='.join(parts[1:]).strip()
                    variable_definitions[variable_name] = variable_value

    return variable_definitions


file_path = 'config.txt'
variables = extract_variable_definitions(file_path)

webhook = variables['webhook']
avatar_url = variables['avatar_url']
icon_url = variables['icon_url']
no_img = variables['no_img']


def remove_spaces(string):
    return string.replace(" ", "")


def discord_send(title, link, SD_description, pub_date, publisher, src_link, website_link, direct_link):
    timezone = pytz.timezone("US/Eastern")
    current_time = datetime.now(timezone).strftime("%m-%d-%Y %I:%M:%S %p")
    startup_webhook = {
        "username": "Zone Monitoring System",
        "avatar_url": f"{avatar_url}",
        "embeds": [
            {
                "title": f"{title}",
                "description": f"{SD_description}",
                "url": f"{link}",
                "color": 262399,
                "thumbnail": {
                    "url": f"{src_link}"
                },
                "fields": [
                    {
                        "name": "Store Name",
                        "value": f"[{website_link}]({direct_link})"
                    },
                    {
                        "name": "Published By",
                        "value": f"{publisher}",
                        "inline": True
                    },
                    {
                        "name": "Published On",
                        "value": f"{pub_date}",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Zone Monitoring Service • {current_time} EST",
                    "icon_url": f"{icon_url}",
                },
            }
        ],
    }
    response = requests.post(webhook, json=startup_webhook)
    print(response)


def SD_Scraper(soup):
    item = soup.find("item")
    title = item.find("title").text.strip()
    SD_link = item.find("link").text.strip()
    SD_description = item.find("description").text.strip()

    try:
        encoded_html = item.find("content:encoded").text
        decoded_html = html.unescape(encoded_html)
        encoded_soup = BeautifulSoup(decoded_html, "html.parser")

        img_tag = encoded_soup.find("img")
        website_links = encoded_soup.find_all("a")

        website_link = "No Store Link Found"
        direct_link = "No Direct Link Found"

        for website in website_links:
            if "data-product-exitwebsite" in website.attrs:
                website_link = website.get("data-product-exitwebsite")
            if "href" in website.attrs:
                url = website.get("href")
                direct_link_parsed = urllib.parse.unquote(url)
                if "&pv=&au=&u2=" in direct_link_parsed:
                    direct_link = urllib.parse.unquote(url).split("&pv=&au=&u2=")[1]
                else:
                    direct_link = remove_spaces(direct_link_parsed)
                break

        src_link = img_tag.get("src") if img_tag else no_img

    except (AttributeError, TypeError):
        print("An error occurred while parsing content:encoded tag.")
        website_link = "No Store Link Found"
        direct_link = "No Direct Link Found"
        src_link = no_img

    pub_date = item.find("pubDate").text.strip()
    publisher = item.find("dc:creator").text.strip()

    return title, SD_link, SD_description, pub_date, publisher, src_link, website_link, direct_link


def main():
    url = "https://slickdeals.net/newsearch.php?searchin=first&forumchoice%5B%5D=9&rss=1"

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "xml")

    title, SD_link, SD_description, pub_date, publisher, src_link, website_link, direct_link = SD_Scraper(soup)
    discord_send(title, SD_link, SD_description, pub_date, publisher, src_link, website_link, direct_link)


def SD_Check_Scraper():
    timezone = pytz.timezone("US/Eastern")
    current_time = datetime.now(timezone).strftime("%m-%d-%Y %I:%M:%S %p")
    url = "https://slickdeals.net/newsearch.php?searchin=first&forumchoice%5B%5D=9&rss=1"

    response = requests.get(url)
    soup = BeautifulSoup(response.content, "xml")

    item = soup.find("item")
    title = item.find("title").text.strip()

    with open("latest_title.txt", "r") as f:
        contents = f.read()
        if title in contents:
            print(f"'{title}' found in the text file. {current_time}")
            return False
        else:
            print(f"New title ('{title}') found, sending webhook. {current_time}")
            with open("latest_title.txt", "w") as w:
                w.write(title)
            return True


while True:
    try:
        if SD_Check_Scraper():
            main()
        else:
            print("Skipping")
        time.sleep(100)
    except Exception as e:
        print('Error has occurred:', e)
        time.sleep(100)
