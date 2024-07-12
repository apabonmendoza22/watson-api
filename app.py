from Flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv
from flask_restful import Api, Resource, fields
import os

# Cargar las variables del archivo .env
load_dotenv()

#crear una instancia de Flask
app = Flask(__name__)
api = Api(app, version='1.0', title='Consulta Ticket API',
          description='API para consultar el estado de un ticket')

ns = api.namespace('tickets', description='Operaciones relacionadas con tickets')

# Definir el modelo para la entrada de datos
ticket_model = api.model('Ticket', {
    'ticket_id': fields.String(required=True, description='El ID del ticket')
})


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

@ns.route('/consulta_ticket')
class TicketResource(Resource):
    @ns.doc('consultar_ticket')
    @ns.expect(ticket_model, validate=True)
    @ns.response(200, 'Success')
    @ns.response(400, 'Invalid Argument')
    @ns.response(500, 'Internal Server Error')
    def get(self):
        '''Consulta el estado de un ticket'''
        ticket_id = request.args.get('ticket_id')
        if ticket_id:
            resultado = consulta_ticket(ticket_id)
            return jsonify({"resultado": resultado})
        else:
            return jsonify({"error": "No ticket_id provided"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)