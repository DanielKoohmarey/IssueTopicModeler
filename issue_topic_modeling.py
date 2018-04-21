# -*- coding: utf-8 -*-
"""
@author: Daniel Koohmarey
@company: Pericror

Copyright (c) Pericror 2018
"""
import lda_topic_modeling
import requests
import pdfkit

def generate_lda_report(instance_prefix, auth, table, field, history, hist_text):
    report = ""
    url = "https://{0}.service-now.com/api/now/table/{1}?sysparm_query={2}" \
            "&sysparm_fields={3}".format(instance_prefix, table, history, field)  
    resp = requests.get(url, auth=auth)
    if resp.status_code == 200:
        results = resp.json()['result']
        docs = []
        for result in results:
            docs.append(result[field].encode('utf-8').split())

        topics = lda_topic_modeling.GetNTopics(docs, 20, 4)
        
        html = "<head><style>td{padding:10px;text-align:left;border: 1px solid #ddd;"\
                "word-wrap:break-word;}tr:nth-of-type(2n){background-color:#f2f2f2;}"\
                "thead{background-color:#00aeef;color:white;cursor:pointer;font-weight:bold}"\
                "table{border-collapse:collapse;}body{padding-left:25px;font-family:Arial;}"\
                "</style></head>"
        html += "<img src = 'https://www.pericror.com/wp-content/uploads/2016/09/"\
                "combination-mark-blue-grey-transparent-background.png'></img>"
        html += "<h1><u>Topic Analysis Report</u></h1>"
        html += "<h4>Instance Prefix: {0}".format(instance_prefix)
        html += "<h4>Table: {0}</h4>".format(table)
        html += "<h4>Field: {0}</h4>".format(field)
        html += "<h4>History: {0}</h4>".format(hist_text)
        html += "<table><thead><tr><td>Topic #</td><td>Topics</td></thead>"
        for topic_num, topic in enumerate(topics):
            html += "<tr><td>{0}</td><td>{1}</td></tr>".format(topic_num+1, topic)
        html += "</table>"            

        report = "{0}_{1}_{2}_topics.pdf".format(instance_prefix, table, field)
        pdfkit.from_string(html, report)
        
    return report
            
if __name__ == '__main__':
    auth = ("user", "pass")
    field = "short_description"
    table= "incident"
    instance_prefix = "prefix"
    generate_lda_report(instance_prefix, auth, table, field)