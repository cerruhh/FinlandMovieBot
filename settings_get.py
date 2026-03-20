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
            user_settings = json.load(settings_file)
            # Merge user_settings into default_settings
            settings = default_settings.copy()
            settings.update(user_settings)
            # Merge nested dictionaries (like 'sources')
            if "sources" in user_settings:
                settings["sources"].update(user_settings["sources"])
            if "banned_genres" in user_settings:
                settings["banned_genres"] = user_settings["banned_genres"]
            if "banned_theaters" in user_settings:
                settings["banned_theaters"] = user_settings["banned_theaters"]

            # If test mode, override only relevant keys
            if settings.get("test"):
                print("Test settings have been activated in settings.json")
                settings["ratings_enabled"] = True
                settings["days_offset"] = 1
                settings["send_mail"] = False
                settings["sources"] = {
                    "finnkino": True,
                    "biorex": False,
                    "kinot.fi": False,
                    "konepaja": False,
                    "gilda": False
                }
                # Optionally, you can also override banned lists for test mode:
                # settings["banned_genres"] = []
                # settings["banned_theaters"] = []

    # Initialize secrets
    if not file_exists("Data/secrets.json"):
        with open("Data/secrets.json", "w") as secret_file:
            json.dump(default_secrets, secret_file, indent=1)
        print("Secrets file not defined, please fill in secrets.json")
        exit(2)

    return settings

