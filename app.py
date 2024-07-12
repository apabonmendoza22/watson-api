from flask import Flask, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint
import requests
import os

app = Flask(__name__)

@app.route('/consulta_ticket', methods=['GET'])
def consulta_ticket():
    ticket_id = request.args.get('ticket_id')
    if ticket_id:
        resultado = consulta_ticket_api(ticket_id)
        return jsonify({"resultado": resultado}), 200
    else:
        return jsonify({"error": "No se proporcionó ticket_id"}), 400

def consulta_ticket_api(ticket_id):
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

# Ruta para servir el archivo swagger.json
@app.route('/swagger.json')
def swagger():
    swagger_content = {
        "openapi": "3.0.3",  # Versión de OpenAPI
        "info": {
            "title": "Consulta Ticket API",
            "version": "1.0",
            "description": "API para consultar el estado de un ticket"
        },
        "paths": {
            "/consulta_ticket": {
                "get": {
                    "summary": "Consulta el estado de un ticket",
                    "parameters": [
                        {
                            "name": "ticket_id",
                            "in": "query",
                            "required": True,
                            "schema": {
                                "type": "string"
                            },
                            "description": "El ID del ticket"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Resultados de la consulta"
                        },
                        "400": {
                            "description": "No se proporcionó ticket_id"
                        }
                    }
                }
            }
        }
    }
    return jsonify(swagger_content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
