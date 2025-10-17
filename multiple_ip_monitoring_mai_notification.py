# This script monitors multiple hosts
# when ever any host is up or down
# this script send mail to reciepients, I used my personal mail server for this project, mail id's work only in my domain

from icmplib import ping
import time
import smtplib
from email.message import EmailMessage
import os
from datetime import datetime
from threading import Thread, Lock 
import csv

# writing a function for mail delivery

def mail(ip, body, result):
    message = EmailMessage()
    sender= "Auto_python_code@srivatsava.com"                    #change sender mail id as per your mail server
    reciepient = ["ubuntu@srivatsava.com","cent@srivatsava.com"]  #change reciepient mail id as per your mail server 
    message['From']= sender
    message['To'] = reciepient 
    message['subject'] = "{} is {}".format(ip, result)
    message.set_content(body)
    mail_server = smtplib.SMTP("192.168.0.3")
    mail_server.login(sender,'password')                     #change your password as per your mail server or pass it as environment variable for security
    mail_server.set_debuglevel(1)
    mail_server.send_message(message)
    mail_server.quit


#save the output files generated into folder
path_to_save = input("enter path to save the output files: ")
out_dir = path_to_save + "ip_monitoring_result"
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

# function to calculate down time duration
def down_duration(ip, up, down):
    duration = up - down
    h,m,s = duration_to_units(duration)
    down_time = f"{h} Hr, {m} min, {s} sec"
    return down_time

def duration_to_units(duration):
    hours, remainder = divmod(duration.total_seconds(), 3600)
    minuts, seconds = divmod(remainder, 60)
    format = f"{hours} Hr, {minuts} min, {seconds} sec"
    return hours, minuts, seconds

# function to create csv file for generating report
def csv_file_generator(ip, up, down, duration):
    data ={}
    data['Date']= datetime.now().strftime("%d/%m/%Y")
    data['Up_at'] = up.strftime("%H:%m:%S")
    data['Down_at']= down.strftime("%H:%m:%S")
    data['Duration']= duration
    all_keys= data.keys()
    list_of_data =[data]
    name = f"{ip} monitor results.csv"
    out_file = os.path.join(out_dir,name)
    with open(out_file,'a+',newline='') as n:
        writer = csv.DictWriter(n,fieldnames=all_keys)
        #if the file is empty write the row header
        if n.tell() == 0:
            writer.writeheader()
        writer.writerow(data)
    
    print(f"Result Updated in {name}")
 
#function to create a log file
def log_file_generator(ip,up,down,duration):
    name = f"{ip} monitor results.log"
    out_file = os.path.join(out_dir,name)
    content = f"{ip} is down at {down},\n up at {up},\n down for duration {duration} \n"
    with open(out_file,'a+') as n:
        n.write(content)
    print(f"added result to {name}")

#appending ip's to be monitores to a list
ip_s = ["10.100.10.1","10.100.10.105","10.100.10.107"]

#using a dictionary to keep track of previous value
previous_value= {ip: None for ip in ip_s}

lock =Lock()
#function to monitoring
def Ping_monitor(ip):
    # using While loop for continous cheking 
    # if host is live assaign current value is UP else Down
    global previous_value
    while(True):
        current_value = ping(ip, count=4, interval=1, timeout=2).is_alive
        with lock:              
            if current_value:
                    current_value_str = "UP"
            else:
                    current_value_str = "DOWN"

            if current_value_str != previous_value[ip]:
                if current_value == "DOWN" and previous_value[ip] != None:
                    Down_at = datetime.now()
                else:
                    up_at = datetime.now()
                
                if previous_value[ip] == "DOWN":
                    duration_val = down_duration(ip, up_at,Down_at)
                    log_file_generator(up_at, Down_at, duration_val)
                    csv_file_generator(up_at, Down_at, duration_val)
           
                if previous_value[ip] != None:
                        x= "{} is {}".format(ip,current_value_str)
                        if current_value_str == "UP":
                            mail_body = f"""
                                <html>
                                    <body>
                                        <h1 style="color:blue";>Ping Monitoring Notification mail </h1>
                                        <p style="color:green"> {ip} is {current_value_str}. </p>
                                        <p>Down Time Duration: {duration_val}</p>
                                        <p>Thanks and Regards</p>
                                    </body>
                                </html>
                                        """
                        elif current_value_str == "DOWN":
                        # Email body for DOWN scenario without duration_val
                            mail_body = f"""
                            <html>
                                <body>
                                    <h1 style="color:blue";>Ping Monitoring Notification mail </h1>
                                    <p style="color:red"> {ip} is {current_value_str}. </p>
                                    <p>Thanks and Regards</p>
                                </body>
                            </html>
                            """
                        print(x)
                        mail(ip, current_value_str,mail_body)
                else :
                        print(f"Started monitoring {ip},\n current status: {current_value_str}")

            previous_value[ip] = current_value_str


if __name__ == "__main__":
    for ip in ip_s:
        executor = Thread(target=Ping_monitor, args=(ip,))
        executor.start()

