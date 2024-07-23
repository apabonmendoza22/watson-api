import os
import requests
import xmltodict
from flask import jsonify

def consultar_incidente(ticket_id):
    usuario = os.getenv('USUARIO')
    contraseña = os.getenv('CONTRASENA')
    url_incidente = os.getenv('URL_INCIDENTE')  # Asegúrate de tener esta URL en tus variables de entorno
    cookie = os.getenv('COOKIE')

    headers = {
        "Content-Type": "text/xml;charset=UTF-8",
        "SOAPAction": "#POST",
        "Cookie": cookie
    }

    soap_body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:max="http://www.ibm.com/maximo">
       <soapenv:Header/>
       <soapenv:Body>
          <max:QueryINPRO>
             <max:INPROQuery>
                <max:WHERE>TICKETID='{ticket_id}'</max:WHERE>
             </max:INPROQuery>
          </max:QueryINPRO>
       </soapenv:Body>
    </soapenv:Envelope>
    """

    response = requests.post(url_incidente, data=soap_body, headers=headers, auth=(usuario, contraseña))
    
    if response.status_code == 200:
        response_dict = xmltodict.parse(response.text)
        try:
            # Comprobar si la ruta esperada existe en response_dict
            in_data = response_dict.get('soapenv:Envelope', {}).get('soapenv:Body', {}).get('QueryINPROResponse', {}).get('INPROSet', {}).get('INCIDENT')
            if not in_data:
                return jsonify({"error": "Datos de IN no encontrados en la respuesta."}), 404
            estado = in_data['STATUS']['#text']
            AFFECTEDPERSON = response_dict['soapenv:Envelope']['soapenv:Body']['QueryINPROResponse']['INPROSet']['INCIDENT']['AFFECTEDPERSON']
            DESCRIPTION = response_dict['soapenv:Envelope']['soapenv:Body']['QueryINPROResponse']['INPROSet']['INCIDENT']['DESCRIPTION']
            DESCRIPTION_LONGDESCRIPTION = response_dict['soapenv:Envelope']['soapenv:Body']['QueryINPROResponse']['INPROSet']['INCIDENT']['DESCRIPTION_LONGDESCRIPTION']
            STATUS = response_dict['soapenv:Envelope']['soapenv:Body']['QueryINPROResponse']['INPROSet']['INCIDENT']['STATUS']

            return jsonify({
                "DESCRIPTION": DESCRIPTION,
                "DESCRIPTION_LONGDESCRIPTION": DESCRIPTION_LONGDESCRIPTION,
                "STATUS": STATUS
                
            }), 200
        except KeyError as e:
            return jsonify({"error": f"Clave no encontrada en la respuesta: {e}"}), 500
    else:
        return jsonify({"error": "Error al consultar el incidente"}), response.status_code