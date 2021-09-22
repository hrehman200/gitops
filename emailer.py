import smtplib
from email.message import EmailMessage

def sendBuildSuccessEmail(cfg, zip_file_on_network, version_xml_path, new_version_num, log_obj):
    global log

    # send email message
    email_message = f"""
        Build Result {zip_file_on_network}
        Build Manifest {version_xml_path}
        Build Log {cfg['PATH_BUILD_LOG']}
    """

    subject = cfg['COMMIT_MESSAGE_PASS'] + ' ' + new_version_num
    to = cfg['SEND_MAIL_DISTRIBUTION_LIST']

    msg = EmailMessage()
    msg.set_content(email_message)
    msg['Subject'] = subject
    msg['From'] = 'sender@gmail.com'
    msg['To'] = to

    with smtplib.SMTP("mail.siemens.de") as server:
        server.send_message(msg)
        log_obj.info(f"""Sent email with subject {subject} to {to}""")


def sendBuildFailEmail(cfg, zip_file_on_network, version_xml_path, new_version_num, log_obj):
    global log

    # send email message
    email_message = f"""
        Build Result {zip_file_on_network}
        Build Manifest {version_xml_path}
        Build Log {cfg['PATH_BUILD_LOG']}
    """

    subject = cfg['COMMIT_MESSAGE_FAIL'] + ' ' + new_version_num
    to = cfg['SEND_MAIL_DISTRIBUTION_LIST']

    msg = EmailMessage()
    msg.set_content(email_message)
    msg['Subject'] = subject
    msg['From'] = 'sender@gmail.com'
    msg['To'] = to

    with smtplib.SMTP("mail.siemens.de") as server:
        server.send_message(msg)
        log_obj.info(f"""Sent email with subject {subject} to {to}""")


def sendNoBuildNeededEmail(cfg, new_version_num, log_obj):
    global log

    # send email message
    email_message = f"""
        No build necessary
    """

    subject = 'Build result: ' + new_version_num
    to = cfg['SEND_MAIL_DISTRIBUTION_LIST']

    msg = EmailMessage()
    msg.set_content(email_message)
    msg['Subject'] = subject
    msg['From'] = 'sender@gmail.com'
    msg['To'] = to

    with smtplib.SMTP("mail.siemens.de") as server:
        server.send_message(msg)
        log_obj.info(f"""Sent email with subject {subject} to {to}""")