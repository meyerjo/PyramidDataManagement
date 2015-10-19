import subprocess
from StringIO import StringIO
from email.mime.text import MIMEText

class MailEvent(object):
    def __init__(self, recipients):
        self.recipients = recipients

    def __call__(self):
        email = MIMEText(self.message)
        email['From'] = 'donotanswer@aclib.net'
        email['To'] = ', '.join(self.recipients)
        email['Subject'] = self.subject
        subprocess.call('sendmail', stdin=StringIO(email.as_string()))

class SuccessMail(MailEvent):
    subject = 'Configuration finished'
    message = '''Dear user,

The configuration has finished.

This is is an automatically generated email, please do not reply.
'''

class FailMail(MailEvent)
    subject = 'Configuration failed'
    message = '''Dear user,

The configuration failed. Some experiments might still be running.

This is is an automatically generated email, please do not reply.
'''

class Shutdown(object):
    def __call__(self):
        subprocess.call('sudo shutdown now', shell=True)
