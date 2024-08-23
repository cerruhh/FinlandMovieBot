from os.path import exists as file_exsits
import json
import colorama

def read_settings():
    """
    get all settings from settings.json
    :return:
    """
    setting_returnable=None
    if not file_exsits("settings.json"):
        with open("settings.json",mode="w+") as settings_file:
            json.dump({
                "ratings_enabled":True,
                "days_offset":2,
                "send_mail":True,
                "sources":{
                    "finnkino":True,
                    "biorex":True,
                    "kinot.fi":True
                }
            },settings_file,indent=2)
    else:
        with open("settings.json",mode="r") as settings_file:
            setting_returnable = json.load(settings_file)
            if setting_returnable["test"]:
                print("test settings have been activated in settings.json")
                setting_returnable = {"ratings_enabled": True, "days_offset": 1, "send_mail": False, "sources": {
                    "finnkino": False, "biorex": False, "kinot.fi": True}}
    # with open("settings.json",mode="ac"):
    #     pass

    if not file_exsits("secrets.json"):
        with open("secrets.json",mode="w+") as secret_file:
            json.dump(
        {
                "email_key": "app_password",
                "sender": "sender@example.com",
                "recipient": "recipient@example.lol",
            },secret_file,indent=1)

            print(colorama.Fore.RED+"secrets file not defined, please fill in secrets.json")
            exit(2)
    return setting_returnable