from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv
import os

# Cargar las variables del archivo .env
load_dotenv()

#crear una instancia de Flask
app = Flask(__name__)

def consulta_ticket(ticket_id):
    usuario = os.getenv('USUARIO')
    contraseña = os.getenv('CONTRASENA')
    url = os.getenv('URL')
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
          <max:QuerySRPRO>
             <max:SRPROQuery>
                <max:WHERE>TICKETID='{ticket_id}'</max:WHERE>
             </max:SRPROQuery>
          </max:QuerySRPRO>
       </soapenv:Body>
    </soapenv:Envelope>
    """

    response = requests.post(url, data=soap_body, headers=headers, auth=(usuario, contraseña))

    if response.status_code == 200:
        return response.text
    else:
        return f"Error: {response.status_code}"

@app.route('/consulta_ticket', methods=['GET'])
def consulta_ticket_api():
    ticket_id = request.args.get('ticket_id')
    if ticket_id:
        resultado = consulta_ticket(ticket_id)
        return jsonify({"resultado": resultado})
    else:
        return jsonify({"error": "No ticket_id provided"}), 400


# si el script se ejecuta correctamente se ejecuta el servidor Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001, debug=True)
