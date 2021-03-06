# -*- coding: utf-8 -*-
"""
@company: Pericror

Notes:
    Run python gmail_wrapper.py --noauth_local_webserver to set up credentials on external machine

Dependencies: 
    sudo pip install --upgrade google-api-python-client
    
Resources used:
    https://developers.google.com/gmail/api/quickstart/python
"""
import httplib2
import os
import argparse
import base64
import mimetypes
import sys

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase

from apiclient import discovery, errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

class GmailWrapper(object):

    SCOPES = 'https://www.googleapis.com/auth/gmail.modify'
    CLIENT_SECRET_FILE = 'client_secret.json' # https://console.developers.google.com/apis/credentials
    APPLICATION_NAME = "Pericror Gmail Monitor"
    AUTHORIZED_FROM = 'info@pericror.com'
    SENDER = 'pericror@gmail.com'

    def __init__(self):
        self.credentials = self.get_credentials()
        self.http = self.credentials.authorize(httplib2.Http())
        self.service = discovery.build('gmail', 'v1', http=self.http)
        
    def refresh_credentials(self, expires_in = 600):
        """Checks if the auth credentials expire soon, and requests new ones if needed
        
        Args:
            expires_in: The number of seconds in the future to check for expiration
            
        Returns:
            datetime, the current credential expiration time
        """
        if self.credentials.get_access_token().expires_in <= expires_in:
            self.credentials.refresh(self.http)
        return self.credentials.get_access_token().expires_in
    
    def get_credentials(self):
        """Gets valid user credentials from storage.
    
        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.
    
        Returns:
            Credentials, the obtained credential.
        """
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()        
        
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'gmail-python-wrapper.json')
    
        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(self.CLIENT_SECRET_FILE, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            credentials = tools.run_flow(flow, store,flags)
            print 'Storing credentials to ' + credential_path
            
        return credentials

    def get_unread_message_id(self):
        """Retrieve the first unread email available.
        
        Returns:
            The message id of the unread email if it exists, otherwise None.
        """
        msg_id = None    
        
        try:
            query = "from:{} is:unread".format(self.AUTHORIZED_FROM)
            response = self.service.users().messages().list(userId='me', maxResults=1,
                                                       q=query).execute()
            if 'messages' in response:
                msg_id = response['messages'][0]['id']

        except errors.HttpError, error:
            print 'An error occurred: %s' % error
            
        return msg_id

    def get_message_data(self, msg_id):
        """Retrieve data from a given email.
        
        Args:
            msg_id: The id of the email message to retrieve the body from.
        
        Returns:
            The email body.
        """
        message_data = {}
        
        try:
            message = self.service.users().messages().get(userId='me', id=msg_id).execute()

            headers = {}
            for header in message['payload']['headers']:
                headers[header['name']] = header['value']
                
            message_data['headers'] = headers

            if 'multipart' in message['payload']['mimeType']:            
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body']['data']
                        break
            else:
                data = message['payload']['body']['data']
                
            message_data['body'] = base64.urlsafe_b64decode(data.encode('ASCII'))
        except Exception as e:
            print 'An error occurred: %s' % e
            
        return message_data

    def mark_as_read(self, msg_id):
        """Mark an email as read.
        
        Args:
            msg_id: The id of the email message to mark as read.
        
        Returns:
            A boolean indicating message has been marked as read successfully.
        """
        success = False
        
        try:
            msg_labels = { "removeLabelIds": ["UNREAD"] }
            message = self.service.users().messages().modify(userId='me', id=msg_id,
                                                        body=msg_labels).execute()
            success = message
            
        except errors.HttpError, error:
            print 'An error occurred: %s' % error 
            
        return success

    def create_message(self, to, subject, plain, html, attachment = None):
        """Create a message for an email.
        
        Args:
            to: The destination of the email message.
            subject: The subject of the email message.
            plain: The text of the email message.
            html: The html of the email message.
            attachment: The path to the attachment.
            
        Returns:
            An object containing a base64url encoded email object.
        """
        message = MIMEMultipart('mixed') # originally 'alternative'
        message['To'] = to
        message['From'] = self.SENDER
        message['Subject'] = subject

        message_text = MIMEMultipart('alternative')
        plain_part = MIMEText(plain, 'plain')
        message_text.attach(plain_part)
        
        html_part = MIMEText(html, 'html')
        message_text.attach(html_part)
        message.attach(message_text)
        
        if attachment:
            content_type, encoding = mimetypes.guess_type(attachment)
    
            msg = None
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'
            main_type, sub_type = content_type.split('/', 1)
            if main_type == 'text':
                fp = open(attachment, 'rb')
                msg = MIMEText(fp.read(), _subtype=sub_type)
                fp.close()
            elif main_type == 'image':
                fp = open(attachment, 'rb')
                msg = MIMEImage(fp.read(), _subtype=sub_type)
                fp.close()
            elif main_type == 'audio':
                fp = open(attachment, 'rb')
                msg = MIMEAudio(fp.read(), _subtype=sub_type)
                fp.close()
            else:
                fp = open(attachment, 'rb')
                msg = MIMEBase(main_type, sub_type)
                msg.set_payload(fp.read())
                fp.close()
            filename = os.path.basename(attachment)
            
            msg.add_header('Content-Disposition', 'attachment', filename=filename)
            message.attach(msg)  
        
        return {'raw': base64.urlsafe_b64encode(message.as_string())}          
        
    def send_message(self, message):
        """Send an email message.
        
        Args:
            message: Message to be sent.
        
        Returns:
            Sent message.
        """
        success = None
          
        try:
            message = (self.service.users().messages().send(userId='me',
                           body=message).execute())
            success = message
        
        except errors.HttpError, error:
            print 'An error occurred: %s' % error 
        
        return success
        
def test():
    wrapper = GmailWrapper()
    # Get an unread (unprocessed) email
    unread_msg_id = wrapper.get_unread_message_id()
    if unread_msg_id:
        # Process the email
        msg_data = wrapper.get_message_data(unread_msg_id)
        msg_body = msg_data['body']
        headers = msg_data['headers']
        print "Processing message from: " + headers['From']
        plain = "Body: {}".format(msg_body)
        html = "<h3>Body:</h3>{}".format(msg_body)
        # Send an email response the contains the original email
        message = wrapper.create_message(headers['From'],
            'Re: ' + headers['Subject'], plain, html, 'test.html')
        wrapper.send_message(message)
        # Mark the message as read so we don't process it again
        wrapper.mark_as_read(unread_msg_id)
        print "Sent email copy to " + headers['From'] 
        
if __name__ == '__main__':
    if 'test' in sys.argv:
        test()
