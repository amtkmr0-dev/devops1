import requests

url = 'https://archives.nseindia.com/content/RSS/Corporate_action.xml'
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}


def fetch_and_save_xml():
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    with open('corporate_action_dump.xml', 'wb') as f:
        f.write(response.content)
    print('XML saved to corporate_action_dump.xml')


if __name__ == '__main__':
    fetch_and_save_xml()
