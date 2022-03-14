# -*- coding: utf-8 -*-

from odoo.tools.translate import _
from odoo import http
from odoo.http import request
from datetime import datetime
from bs4 import BeautifulSoup
import json
import sys
import uuid
from odoo import http
from odoo.http import request, Response
import jsonschema
from jsonschema import validate
import json
import yaml
import requests, json
import logging

_logger = logging.getLogger(__name__)
from datetime import timedelta, datetime, date


class OdooController(http.Controller):

    @http.route('/tpco/odoo/ws003', auth="public", type="json", method=['POST'], csrf=False)
    def activo_query(self, **post):

        post = json.loads(request.httprequest.data)
        res = {}
        as_token = uuid.uuid4().hex
        mensaje_error = {
            "Token": as_token,
            "RespCode": -1,
            "RespMessage": "Error de conexión"
        }
        mensaje_correcto = {
            "Token": as_token,
            "RespCode": 0,
            "RespMessage": "OC recibidas correctamente"
        }
        try:
            myapikey = request.httprequest.headers.get("Authorization")
            if not myapikey:
                mensaje_error['RespCode'] = -2
                mensaje_error['RespMessage'] = f"Rechazado: API KEY no existe"
                return mensaje_error

            user_id = request.env["res.users.apikeys"]._check_credentials(scope="rpc", key=myapikey)
            request.uid = user_id

            if post['params']:
                post = post['params']
                vals = {}
                lot = request.env['stock.production.lot'].sudo().search([('name', '=', post['EPCCode'])], limit=1)
                if lot:
                    location_id = None
                    location_parent_id = None
                    product_id = lot.product_id

                    for quant in lot.quant_ids:
                        location_id = quant.location_id
                        location_parent_id = quant.location_id.location_id

                    vals.update({
                        'idHandheld': post['idHandheld'],
                        'ubicacionPadre': location_parent_id.name,
                        'ubicacion': location_id.name,
                        'EPCCode': lot.name,
                        'SKU': product_id.default_code,
                        'nombreActivo': product_id.name,
                        'tipoPrenda': product_id.tipo_prenda_id.name,
                        'marca': product_id.marca_id.name,
                        'tamaño': product_id.tamanno_id.name,
                        'origen': product_id.origen_id.name,
                        'color': product_id.color_id.name,
                        'genero': product_id.genero_id.name,
                        'codigo': 0,
                        'mensaje': 'Activo existente en el inventario',

                    })
                else:
                    vals.update({
                        'idHandheld': post['idHandheld'],
                        'codigo': -1,
                        'mensaje': 'Activo no existe en el inventario',
                    })
                return vals

        except Exception as e:
            mensaje_error = {
                "Token": as_token,
                "RespCode": -5,
                "RespMessage": "Rechazado: Autenticación fallida"
            }
            mensaje_error['RespMessage'] = f"Error: {str(e)}"
            return mensaje_error
