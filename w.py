import requests


def send(url, title, discription, content):
    data = {
        "username": "Roy User Backup",
        "content": content,
        "avatar_url": "https://cdn.discordapp.com/icons/924226396547596319/2b3f24a96d7ed9a99951b7a7e4fa038c.png?size=4096"

    }

    data["embeds"] = [
        {
            "description": discription,
            "title": title,
            "color": 0x5c6cdf

        }
    ]

    result = requests.post(url, json=data)

    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
    else:
        print("Payload delivered successfully, code {}.".format(result.status_code))

