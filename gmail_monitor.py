# -*- coding: utf-8 -*-
"""
@author: Daniel Koohmarey
@company: Pericror

Copyright (c) Pericror 2018
"""
import pericror_gmail_wrapper
import issue_topic_modeling
import time

def handle_topic_request(wrapper, msg_fields):
    success = False
    print "Handling topic report form submission!"
    try:
        print "Instance Prefix: {0}\nAuth: {1}\nTable: {2}\nCTable: {3}\n"\
            "Field: {4}\nCField: {5}\nHistory: {6}\nHistory Label:{7}\nEmail: {8}".format(
            msg_fields['prefix'],(msg_fields['user'],msg_fields['pass']), msg_fields['table'],
            msg_fields['ctable'], msg_fields['field'], msg_fields['cfield'],
            msg_fields['history'], msg_fields['history_label'], msg_fields['email'])
    except KeyError as e:
        print "Missing submission field: {0}!".format(e.args[0])
        return

    if msg_fields['ctable']:
        msg_fields['table'] = msg_fields['ctable']
        
    if msg_fields['cfield']:
        msg_fields['field'] = msg_fields['cfield']
        
    report = issue_topic_modeling.generate_lda_report(msg_fields['prefix'],
                                                      (msg_fields['user'],msg_fields['pass']),
                                                        msg_fields['table'], msg_fields['field'],
                                                        msg_fields['history'], msg_fields['history_label'])
                                                        
    if report:
        plain = "Hello, your topic report has been completed and is attached. For more information"\
            " on interpreting results, see https://www.pericror.com/servicenow/taking-action-results-topic-analysis."\
            " We appreciate your business, and if you have any questions or concerns, contact us at support@pericror.com."
        html = "Hello,<br>&nbsp;&nbsp;&nbsp;Your topic report has been completed and is attached. For more information"\
            " on interpreting results, see https://www.pericror.com/servicenow/taking-action-results-topic-analysis."\
            "We appreciate your business, and if you have any questions or concerns, contact us at support@pericror.com."\
            "Thanks,<br>- The Pericror Team"
        message = wrapper.create_message(msg_fields['email'], "Pericror Topic Results", plain, html, report)
        wrapper.send_message(message)
        print "Sent results to {}!".format(msg_fields['email'])
        success = True
    else:
        print "Warning: Failed to create report!"
    return success

if __name__ == '__main__':        
    msg_handlers = {
                    '[Form Submission] Topic Report' : handle_topic_request    
                }    
    
    wrapper = pericror_gmail_wrapper.GmailWrapper()
    while True:
        # Ensure our auth credentials are still valid
        wrapper.refresh_credentials()
        
        # Get an unread (unprocessed) email
        unread_msg_id = wrapper.get_unread_message_id()
        
        if not unread_msg_id:
            time.sleep(300)
            continue
        
        # Process the email
        msg_data = wrapper.get_message_data(unread_msg_id)
        
        headers = msg_data['headers']
        msg_body = msg_data['body'].split('\n')
        msg_body = [elem.rstrip('\r') for elem in msg_body]
        msg_fields = {}
        for line in msg_body:
            if ":" in line:
                msg_fields[line[:line.find(":")]] = line[line.find(":")+1:]
            
        if 'Subject' not in headers or headers['Subject'] not in msg_handlers:
            wrapper.mark_as_read(unread_msg_id)
            time.sleep(300)
            continue
        
        msg_handlers[headers['Subject']](wrapper, msg_fields)
        
        # Mark the message as read so we don't process it again
        wrapper.mark_as_read(unread_msg_id)
            
        print "Sleeping 5 minutes before checking again..."
        time.sleep(300) # sleep 5 minutes before checking again
