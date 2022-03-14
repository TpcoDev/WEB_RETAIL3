# -*- coding: utf-8 -*-

import uuid
from odoo import http
from odoo.http import request, Response
import jsonschema
from jsonschema import validate
import json


class ListaUbicacionesController(http.Controller):

    @http.route('/tpco/odoo/ws006', auth="public", type="json", method=['POST'], csrf=False)
    def lista_ubicaciones(self, **post):

        post = json.loads(request.httprequest.data)
        res = {}
        as_token = uuid.uuid4().hex
       

        try:
            myapikey = request.httprequest.headers.get("Authorization")
            if not myapikey:
                mensaje_error['RespCode'] = -2
                mensaje_error['RespMessage'] = f"Rechazado: API KEY no existe"
                return mensaje_error

            user_id = request.env["res.users.apikeys"]._check_credentials(scope="rpc", key=myapikey)
            request.uid = user_id
            if user_id:
                res['token'] = as_token

                stock_location = request.env['stock.location']
                objs_stock_location = stock_location.search([('usage',"=",'internal')])
                detalleubicaciones = []
                ubicacion_padre = ""
                for obj in objs_stock_location:
                    if obj.location_id.name:
                        ubicacion_padre = obj.location_id.name

                    detalleubicaciones.append({'ubicacionPadre':ubicacion_padre,'ubicacion':obj.name})

                return {
                    "user":post['params']['user'],
                    "detalleUbicaciones":detalleubicaciones
                }

        except Exception as e:
            mensaje_error = {
                "Token": as_token,
                "RespCode": -5,
                "RespMessage": "Rechazado: Autenticación fallida"
            }
            mensaje_error['RespMessage'] = f"Error: {str(e)}"
            return mensaje_error
