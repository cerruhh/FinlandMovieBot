import smtplib as smtp
from os.path import basename
from os.path import abspath
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import datetime
import json
searchString=(datetime.datetime.now()+datetime.timedelta(1)).strftime("%d.%m.%Y")
def returnUserData():
    with open(file="secrets.json",encoding="UTF-8",mode="r+",newline=None) as file:
        try:
            f=json.load(file)
            emk=f["email_key"]
            repc=f["recipient"]
            sender=f["sender"]
            return f

        except(KeyError,IndexError,json.JSONDecodeError):
            key=input("Define your email key? ")
            sender=input("Define sender email adress: ")
            recipient=input("Define email recipient (type m+ to send to self): ")

            json.dump({
                "email_key":key,
                "sender":sender,
                "recipient":recipient
            },file,indent=1)
            print("Please re-run the python script.\n ")
            exit(4002)






FILE_LIST=[
    "Data/output.csv",
    "Data/output.txt",
    "Data/output.xlsx",
    # "Data/tomato.json",
    # "Data/finnkino.json"
]



def SendMail():
    user_data=returnUserData()

    body=f"De Finkino lijst van {searchString}"
    KEY =user_data["email_key"]
    SENDER = user_data["sender"]
    RECIPIENT = user_data["recipient"]
    print(f"verzonden naar: {RECIPIENT} vanaf {SENDER} ")
    SUBJECT = f"Finkino Film List op {searchString}"
    #note pad ++ is een heel goede progamma :)
    msg=MIMEMultipart()
    msg.set_charset("utf8")
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    msg["Subject"]=SUBJECT
    msg.attach(MIMEText(body, 'plain'))
    for flname in FILE_LIST:
        with open(file=abspath(flname), mode="rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(flname)
            )
            print("sending file: " + basename(flname))

        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(flname)
        msg.attach(part)
    con=smtp.SMTP("smtp.gmail.com", port=587)
    con.starttls()
    con.login(user=SENDER, password=KEY)
    con.sendmail(SENDER,RECIPIENT,msg.as_string())
    con.close()
    print("Mail has been sent")