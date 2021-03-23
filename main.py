import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from datetime import datetime
import calendar
import smtplib
import os

pi_hole_ip = 'http://localhost'
mydate = datetime.now()
year = datetime.now().year
month = datetime.now().month
curr_day = datetime.now().day
_, daysOfThisMonth = calendar.monthrange(year, month)


def generate_report():
    """
    generate report between last and current month
    """
    data = {}
    with open('data/prev_month.json') as prev_month_json:
        data['prev_month'] = json.load(prev_month_json)
    data['curr_month'] = curr_month

    with open('email_template.txt', 'r') as reader:
        html = reader.read()

    html = html.replace("{{report_for_month}}", mydate.strftime("%B") + " " + str(year))

    html = html.replace("{{prev_month_domains_blocked}}", str(data['prev_month'].get('domains_being_blocked')))
    html = html.replace("{{this_month_domains_blocked}}", str(data['curr_month'].get('domains_being_blocked')))
    html = html.replace("{{diff_month_domains_blocked}}", str(
        data['curr_month'].get('domains_being_blocked') - data['prev_month'].get('domains_being_blocked')))

    html = html.replace("{{prev_month_ads_blocked}}", str(data['prev_month'].get('ads_blocked_today')))
    html = html.replace("{{this_month_ads_blocked}}", str(data['curr_month'].get('ads_blocked_today')))
    html = html.replace("{{diff_month_ads_blocked}}",
                        str(data['curr_month'].get('ads_blocked_today') - data['prev_month'].get('ads_blocked_today')))

    html = html.replace("{{prev_month_ads_percentage}}", str(data['prev_month'].get('ads_percentage_today')))
    html = html.replace("{{this_month_ads_percentage}}", str(data['curr_month'].get('ads_percentage_today')))
    html = html.replace("{{diff_month_ads_percentage}}", str(
        data['curr_month'].get('ads_percentage_today') - data['prev_month'].get('ads_percentage_today')))

    html = html.replace("{{prev_month_unique_domains}}", str(data['prev_month'].get('unique_domains')))
    html = html.replace("{{this_month_unique_domains}}", str(data['curr_month'].get('unique_domains')))
    html = html.replace("{{diff_month_unique_domains}}",
                        str(data['curr_month'].get('unique_domains') - data['prev_month'].get('unique_domains')))

    html = html.replace("{{prev_month_clients_ever_seen}}", str(data['prev_month'].get('clients_ever_seen')))
    html = html.replace("{{this_month_clients_ever_seen}}", str(data['curr_month'].get('clients_ever_seen')))
    html = html.replace("{{diff_month_clients_ever_seen}}",
                        str(data['curr_month'].get('clients_ever_seen') - data['prev_month'].get('clients_ever_seen')))

    html = html.replace("{{prev_month_unique_clients}}", str(data['prev_month'].get('unique_clients')))
    html = html.replace("{{this_month_unique_clients}}", str(data['curr_month'].get('unique_clients')))
    html = html.replace("{{diff_month_unique_clients}}",
                        str(data['curr_month'].get('unique_clients') - data['prev_month'].get('unique_clients')))

    return html


def purge_data():
    os.rename('data/curr_month.json', 'data/prev_month.json')
    with open('data/curr_month.json', 'w') as json_file:
        json.dump({"domains_being_blocked": 0, "ads_blocked_today": 0, "ads_percentage_today": 0,
                   "unique_domains": 0, "clients_ever_seen": 0, "unique_clients": 0, "month": month}, json_file)


def send_report():
    """
    Sends an Email with information and comparative report between current and previous month
    """

    message = generate_report()

    email_from = os.environ.get("SENDER_EMAIL", None)
    password = os.environ.get("EMAIL_PASSWORD", None)
    send_to_email = os.environ.get("RECEIVER_EMAIL", None)

    msg = MIMEMultipart()
    msg["From"] = email_from
    msg["To"] = send_to_email
    msg["Subject"] = f'Report for {mydate.strftime("%B")} {year} 👨🏽‍💼'

    msg.attach(MIMEText(message, 'html'))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email_from, password)
    text = msg.as_string()
    server.sendmail(email_from, send_to_email, text)
    server.quit()


try:

    with open('data/curr_month.json') as json_file:
        curr_month = json.load(json_file)

    r = requests.get(f'{pi_hole_ip}/admin/api.php?summaryRaw', timeout=1)
    print(r.status_code)
    data = r.json()

    if r.status_code == 200:
        curr_month['domains_being_blocked'] = data.get('domains_being_blocked')
        curr_month['ads_blocked_today'] = curr_month['ads_blocked_today'] + data.get('ads_blocked_today')
        curr_month['ads_blocked_today'] = curr_month['ads_blocked_today'] + data.get('ads_blocked_today')
        curr_month['unique_domains'] = data.get('unique_domains')
        curr_month['clients_ever_seen'] = data.get('clients_ever_seen')
        curr_month['unique_clients'] = data.get('unique_clients')
        curr_month['month'] = datetime.now().month

        if daysOfThisMonth == curr_day:
            curr_month['ads_percentage_today'] = (curr_month['ads_percentage_today'] + data.get(
                'ads_percentage_today')) / daysOfThisMonth
        else:
            curr_month['ads_percentage_today'] = curr_month['ads_percentage_today'] + data.get('ads_percentage_today')

        with open('data/curr_month.json', 'w') as outfile:
            json.dump(curr_month, outfile)

        if daysOfThisMonth == curr_day:
            send_report()
            purge_data()

except requests.exceptions.RequestException as e:
    raise SystemExit(e)
