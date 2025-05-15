import json
from os.path import exists as file_exists

def read_settings():
    """
    Get all settings from settings.json and secrets.json.
    :return: Dictionary containing settings.
    """
    default_settings = {
        "test": False,
        "ratings_enabled": True,
        "days_offset": 1,
        "send_mail": True,
        "sources": {
            "finnkino": True,
            "biorex": True,
            "kinot.fi": True,
            "konepaja": True,
            "gilda": True
        }
    }

    default_secrets = {
        "email_key": "app_password",
        "sender": "sender@example.com",
        "recipient": "recipient@example.lol"
    }

    # Initialize settings
    if not file_exists("settings.json"):
        with open("settings.json", "w") as settings_file:
            json.dump(default_settings, settings_file, indent=2)
        settings = default_settings
    else:
        with open("settings.json", "r") as settings_file:
            settings = json.load(settings_file)
            if settings.get("test"):
                print("Test settings have been activated in settings.json")
                settings = {
                    "ratings_enabled": True,
                    "days_offset": 1,
                    "send_mail": False,
                    "sources": {
                        "finnkino": True,
                        "biorex": False,
                        "kinot.fi": False,
                        "konepaja": False,
                        "gilda": False
                    }
                }

    # Initialize secrets
    if not file_exists("secrets.json"):
        with open("secrets.json", "w") as secret_file:
            json.dump(default_secrets, secret_file, indent=1)
        print("Secrets file not defined, please fill in secrets.json")
        exit(2)

    return settings

