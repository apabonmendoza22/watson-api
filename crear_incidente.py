import os
import requests
import xmltodict
from flask import jsonify, request
import xml.etree.ElementTree as ET

def crear_incidente ():
    data = request.json
    soap_body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:max="http://www.ibm.com/maximo">
        <soapenv:Header/>
        <soapenv:Body>
            <max:CreateINPRO>
                <max:INPROSet>
                    <max:Incident>
                        <max:REPORTEDBY>{data['reportedBy']}</max:REPORTEDBY>
                        <max:AFFECTEDPERSON>{data['affectedPerson']}</max:AFFECTEDPERSON>
                        <max:DESCRIPTION>{data['description']}</max:DESCRIPTION>
                        <max:DESCRIPTION_LONGDESCRIPTION>{data['longDescription']}</max:DESCRIPTION_LONGDESCRIPTION>
                        <max:EXTERNALSYSTEM>{data['externalSystem']}</max:EXTERNALSYSTEM>
                        <max:OWNERGROUP>{data['ownerGroup']}</max:OWNERGROUP>
                        <max:CLASSIFICATIONID>{data['classificationId']}</max:CLASSIFICATIONID>
                        <max:IMPACT>{data['impact']}</max:IMPACT>
                        <max:URGENCY>{data['urgency']}</max:URGENCY>
                    </max:Incident>
                </max:INPROSet>
            </max:CreateINPRO>
        </soapenv:Body>
    </soapenv:Envelope>
    """
    url = os.getenv('URL_INCIDENTE')
    headers = {"Content-Type": "text/xml;charset=UTF-8", "SOAPAction": "CreateSRPRO"}
    response = requests.post(url, data=soap_body, headers=headers, auth=(os.getenv('USUARIO'), os.getenv('CONTRASENA')))

    root = ET.fromstring(response.text)

    ns = {'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/', 'max': 'http://www.ibm.com/maximo'}
    ticket_id = root.find('.//max:TICKETID', ns).text
    
    if response.status_code == 200:
        return jsonify({"ticketId": ticket_id}), 200
    else:
        return jsonify({"error": "Error al crear el incidente"}), response.status_code