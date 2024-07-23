from flask import Flask, jsonify, request
import requests
import os
import xmltodict
import json
import xml.etree.ElementTree as ET
from consulta_incidente import consultar_incidente
from crear_incidente import crear_incidente


app = Flask(__name__)

@app.route('/consultar_incidente', methods=['GET'])
def api_consultar_incidente():
    ticket_id = request.args.get('ticket_id')
    
    if ticket_id:
        return consultar_incidente(ticket_id)
    else:
        return jsonify({"error": "No se proporcionó ticket_id"}), 400
    

@app.route('/crear_incidente', methods=['POST'])
def api_crear_incidente():
    return crear_incidente()



@app.route('/consulta_ticket', methods=['GET'])
def consulta_ticket():
    ticket_id = request.args.get('ticket_id')
    
    if ticket_id:
        resultado = consulta_ticket_api(ticket_id)
        # Adjust the response structure to include 'response' as per Swagger documentation
        return jsonify({"response": {"resultado": resultado}}), 200
    else:
        return jsonify({"error": "No se proporcionó ticket_id"}), 400


@app.route('/crear_ticket', methods=['POST'])
def crear_ticket():
    data = request.json
    soap_body = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:max="http://www.ibm.com/maximo">
        <soapenv:Header/>
        <soapenv:Body>
            <max:CreateSRPRO>
                <max:SRPROSet>
                    <max:SR>
                        <max:REPORTEDBY>{data['reportedBy']}</max:REPORTEDBY>
                        <max:AFFECTEDPERSON>{data['affectedPerson']}</max:AFFECTEDPERSON>
                        <max:DESCRIPTION>{data['description']}</max:DESCRIPTION>
                        <max:DESCRIPTION_LONGDESCRIPTION>{data['longDescription']}</max:DESCRIPTION_LONGDESCRIPTION>
                        <max:EXTERNALSYSTEM>{data['externalSystem']}</max:EXTERNALSYSTEM>
                        <max:OWNERGROUP>{data['ownerGroup']}</max:OWNERGROUP>
                        <max:OWNER>{data['owner']}</max:OWNER>
                        <max:CLASSIFICATIONID>{data['classificationId']}</max:CLASSIFICATIONID>
                        <max:IMPACT>{data['impact']}</max:IMPACT>
                        <max:URGENCY>{data['urgency']}</max:URGENCY>
                    </max:SR>
                </max:SRPROSet>
            </max:CreateSRPRO>
        </soapenv:Body>
    </soapenv:Envelope>
    """
    url = os.getenv('URL')
    headers = {"Content-Type": "text/xml;charset=UTF-8", "SOAPAction": "CreateSRPRO"}
    response = requests.post(url, data=soap_body, headers=headers, auth=(os.getenv('USUARIO'), os.getenv('CONTRASENA')))

    root = ET.fromstring(response.text)

    ns = {'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/', 'max': 'http://www.ibm.com/maximo'}
    ticket_id = root.find('.//max:TICKETID', ns).text
    
    if response.status_code == 200:
        return jsonify({"ticketId": ticket_id}), 200
    else:
        return jsonify({"error": "Error al crear el ticket"}), response.status_code



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
        response_dict = xmltodict.parse(response.text)
        try:

            # Comprobar si la ruta esperada existe en response_dict
            sr_data = response_dict.get('soapenv:Envelope', {}).get('soapenv:Body', {}).get('QuerySRPROResponse', {}).get('SRPROSet', {}).get('SR')
            if not sr_data:
                return {"error": "Datos de SR no encontrados en la respuesta."}
            estado = response_dict['soapenv:Envelope']['soapenv:Body']['QuerySRPROResponse']['SRPROSet']['SR']['STATUS']['#text']
            ticketID = response_dict['soapenv:Envelope']['soapenv:Body']['QuerySRPROResponse']['SRPROSet']['SR']['TICKETID']
            description = response_dict['soapenv:Envelope']['soapenv:Body']['QuerySRPROResponse']['SRPROSet']['SR']['DESCRIPTION']
            long_description = response_dict['soapenv:Envelope']['soapenv:Body']['QuerySRPROResponse']['SRPROSet']['SR']['DESCRIPTION_LONGDESCRIPTION']
            ownergroup = response_dict['soapenv:Envelope']['soapenv:Body']['QuerySRPROResponse']['SRPROSet']['SR']['OWNERGROUP']
            
            # Verificar si hay worklogs y normalizar a una lista
            worklogs = response_dict['soapenv:Envelope']['soapenv:Body']['QuerySRPROResponse']['SRPROSet']['SR'].get('WORKLOG')
            worklogs_info = [
                {"RESUMEN_WORKLOG": "No disponible", "DETALLE_WORKLOG": "No disponible", "FECHA_CREACION_WORKLOG": "No disponible"},
                {"RESUMEN_WORKLOG": "No disponible", "DETALLE_WORKLOG": "No disponible", "FECHA_CREACION_WORKLOG": "No disponible"},
                {"RESUMEN_WORKLOG": "No disponible", "DETALLE_WORKLOG": "No disponible", "FECHA_CREACION_WORKLOG": "No disponible"}
]           
            if worklogs:
                if not isinstance(worklogs, list):  # Si no es una lista, convertir a lista
                    worklogs = [worklogs]
                # Seleccionar solo los últimos tres worklogs si hay más de tres
                worklogs = worklogs[-3:]
                for i, wl in enumerate(worklogs):
                    worklogs_info[i] = {
                        "RESUMEN_WORKLOG": wl.get('DESCRIPTION', "No disponible"),
                        "DETALLE_WORKLOG": wl.get('DESCRIPTION_LONGDESCRIPTION', "No disponible"),
                        "FECHA_CREACION_WORKLOG": wl.get('CREATEDATE', "No disponible")
                    }

            return {
                "TICKET": ticketID,
                "ESTADO": estado,
                "RESUMEN": description,
                "DETALLE": long_description,
                "GRUPO_RESOLUTOR": ownergroup,
                "WORKLOGS": worklogs_info
            }

        except KeyError:
            return {"error": "La propiedad especificada no fue encontrada en la respuesta."}
    else:
        return {"error": f"Error: {response.status_code}"}


    
# Ruta para servir el archivo swagger.json
@app.route('/swagger.json')
def swagger():
    swagger_content = {
        "openapi": "3.0.3",  # Versión de OpenAPI
        "info": {
            "title": "Consulta Ticket API",
            "version": "1.0",
            "description": "API para consultar y crear tickets"
        },
        "servers": [
            {
                "url": "http://3.144.157.89:5001"
            }
        ],
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
                            "description": "Resultados de la consulta",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "response": {
                                                "type": "string",
                                                "description": "Resultado de la consulta"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "No se proporcionó ticket_id",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "error": {
                                                "type": "string",
                                                "description": "Mensaje de error"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/crear_ticket": {
                "post": {
                    "summary": "Crea un nuevo ticket",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "reportedBy": {
                                            "type": "string",
                                            "description": "Quién reporta el ticket"
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Descripción del ticket"
                                        },
                                        "longDescription": {
                                            "type": "string",
                                            "description": "Descripción detallada del ticket"
                                        },
                                        "affectedPerson": {
                                            "type": "string",
                                            "description": "Persona afectada"
                                        },
                                        "externalSystem": {
                                            "type": "string",
                                            "description": "Sistema externo"
                                        },
                                        "ownerGroup": {
                                            "type": "string",
                                            "description": "Grupo responsable"
                                        },
                                        "owner": {
                                            "type": "string",
                                            "description": "Responsable"
                                        },
                                        "classificationId": {
                                            "type": "string",
                                            "description": "ID de clasificación"
                                        },
                                        "impact": {
                                            "type": "integer",
                                            "description": "Impacto"
                                        },
                                        "urgency": {
                                            "type": "integer",
                                            "description": "Urgencia"
                                        }

                                    },
                                    "required": [
                                        "reportedBy",
                                        "affectedPerson",
                                        "description",
                                        "longDescription",
                                        "externalSystem",
                                        "ownerGroup",
                                        "owner",
                                        "classificationId",
                                        "impact",
                                        "urgency"

                                    ]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Ticket creado exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "ticketId": {
                                                "type": "string",
                                                "description": "El ID del ticket creado"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Error al crear el ticket",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "error": {
                                                "type": "string",
                                                "description": "Mensaje de error"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/crear_incidente": {
                "post": {
                    "summary": "Crea un nuevo incidente",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "reportedBy": {
                                            "type": "string",
                                            "description": "Quién reporta el ticket"
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "Descripción del ticket"
                                        },
                                        "longDescription": {
                                            "type": "string",
                                            "description": "Descripción detallada del ticket"
                                        },
                                        "affectedPerson": {
                                            "type": "string",
                                            "description": "Persona afectada"
                                        },
                                        "externalSystem": {
                                            "type": "string",
                                            "description": "Sistema externo"
                                        },
                                        "ownerGroup": {
                                            "type": "string",
                                            "description": "Grupo responsable"
                                        },
                                        "classificationId": {
                                            "type": "string",
                                            "description": "ID de clasificación"
                                        },
                                        "impact": {
                                            "type": "integer",
                                            "description": "Impacto"
                                        },
                                        "urgency": {
                                            "type": "integer",
                                            "description": "Urgencia"
                                        }

                                    },
                                    "required": [
                                        "reportedBy",
                                        "affectedPerson",
                                        "description",
                                        "longDescription",
                                        "externalSystem",
                                        "ownerGroup",
                                        "classificationId",
                                        "impact",
                                        "urgency"

                                    ]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Ticket creado exitosamente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "ticketId": {
                                                "type": "string",
                                                "description": "El ID del ticket creado"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Error al crear el ticket",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "error": {
                                                "type": "string",
                                                "description": "Mensaje de error"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/consulta_incidente": {
                "get": {
                    "summary": "Consulta el estado de un incidente",
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
                            "description": "Resultados de la consulta",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "response": {
                                                "type": "string",
                                                "description": "Resultado de la consulta"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "No se proporcionó ticket_id",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "error": {
                                                "type": "string",
                                                "description": "Mensaje de error"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },



        }
    }
    return jsonify(swagger_content)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
