# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID
from odoo.tools.translate import _
from odoo import http
from odoo.http import request
from datetime import datetime
from bs4 import BeautifulSoup
import json
import sys
import base64
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

MESSAGES = {
    '0': 'Activo existe',
    '1': 'Activo faltante en inventario',
    '2': 'Activo sobrante en inventario',
    '9': 'Activo no esta en el sistema',
}


class OdooController(http.Controller):

    @http.route('/tpco/odoo/ws005', auth="public", type="json", method=['POST'], csrf=False)
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
            "RespMessage": "Activo existe"
        }
        try:
            myapikey = request.httprequest.headers.get("Authorization")
            if not myapikey:
                mensaje_error['RespCode'] = -2
                mensaje_error['RespMessage'] = f"Rechazado: API KEY no existe"
                return mensaje_error

            user_id = request.env["res.users.apikeys"]._check_credentials(scope="rpc", key=myapikey)
            request.uid = user_id or SUPERUSER_ID

            if user_id and post['params']:
                post = post['params']
                vals = {
                    'idConciliacion': '',
                    'fechaOperacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'ubicacion': post['ubicacion'],
                    'ubicacionPadre': post['ubicacionPadre'],
                    'user': post['user'],
                    'detalleActivos': []
                }

                domain = []
                data = {
                    'epc_activo_existe': [],
                    'epc_activo_faltante': [],
                    'epc_activo_sobrante': [],
                    'epc_activo_no_esta': []
                }
                location_parent_id = None
                location_id = None

                location_parent_id = request.env['stock.location'].sudo().search(
                    [('name', '=', post['ubicacionPadre'])], limit=1)
                location_id = request.env['stock.location'].sudo().search([('name', '=', post['ubicacion'])],
                                                                          limit=1)
                if location_parent_id:
                    location_id = request.env['stock.location'].sudo().search(
                        [('name', '=', post['ubicacion']), ('location_id', '=', location_parent_id.id)],
                        limit=1)

                quants = request.env['stock.quant'].sudo().search([])

                epcodes = []
                for detalle in post['detalleActivos']:
                    epcodes.append(detalle['EPCCode'])

                epc_activo_existe = []
                epc_activo_faltante = []
                epc_activo_sobrante = []
                epc_activo_no_esta = []

                # Fill list exixsts
                for code in epcodes:
                    quant_exists = quants.filtered(
                        lambda x: x.lot_id.name == code and x.location_id.id == location_id.id).mapped(
                        'lot_id.name')
                    quant_faltantes = quants.filtered(
                        lambda x: x.lot_id.name == code and x.location_id.id != location_id.id).mapped('lot_id.name')
                    quant_not_exists = quants.filtered(lambda x: x.lot_id.name == code)

                    if len(quant_exists):
                        epc_activo_existe.append(quant_exists[0])
                    if len(quant_faltantes):
                        epc_activo_faltante.append(quant_faltantes[0])
                    if not len(quant_not_exists):
                        epc_activo_no_esta.append(code)

                epc_activo_sobrante = request.env['stock.quant'].sudo().search(
                    [('lot_id.name', 'not in', epcodes), ('location_id', '=', location_id.id)])
                epc_activo_sobrante = epc_activo_sobrante.filtered(lambda x: x.available_quantity > 0).mapped(
                    'lot_id.name')

                for item in epc_activo_existe:
                    vals['detalleActivos'].append({
                        'EPCCode': item,
                        'codigo': '0',
                        'mensaje': MESSAGES['0'],
                    })
                    data['epc_activo_existe'].append(item)

                for item in epc_activo_faltante:
                    vals['detalleActivos'].append({
                        'EPCCode': item,
                        'codigo': '1',
                        'mensaje': MESSAGES['1'],
                    })
                    data['epc_activo_faltante'].append(item)

                for item in epc_activo_sobrante:
                    vals['detalleActivos'].append({
                        'EPCCode': item,
                        'codigo': '2',
                        'mensaje': MESSAGES['2'],
                    })
                    data['epc_activo_sobrante'].append(item)

                for item in epc_activo_no_esta:
                    vals['detalleActivos'].append({
                        'EPCCode': item,
                        'codigo': '9',
                        'mensaje': MESSAGES['9'],
                    })
                    data['epc_activo_no_esta'].append(item)

                data['id_conciliacion'] = ''
                data['fecha'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                data['ubicacion'] = post['ubicacion']
                data['user'] = post['user']

                data['resumen_epc_activo_existe'] = len(epc_activo_existe)
                data['resumen_epc_activo_faltante'] = len(epc_activo_faltante)
                data['resumen_epc_activo_sobrante'] = len(epc_activo_sobrante)
                data['resumen_epc_activo_no_esta'] = len(epc_activo_no_esta)

                datas = {
                    'data': data
                }

                user = request.env['res.users'].sudo().search([('name', '=', post['user'])], limit=1)
                if user:
                    report_template_id = request.env.ref(
                        'ws_activos_conciliation.report_assets_conciliation_pdf_action').sudo()._render_qweb_pdf(
                        res_ids=quants.ids[0], data=datas)

                    data_record = base64.b64encode(report_template_id[0])
                    date_str = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
                    ir_values = {
                        'name': f'rep_conciliacion_{date_str}_{post["ubicacion"]}    ',
                        'type': 'binary',
                        'datas': data_record,
                        'store_fname': data_record,
                        'mimetype': 'application/x-pdf',
                    }
                    data_id = request.env['ir.attachment'].sudo().create(ir_values)
                    # create a mail_mail based on values, without attachments
                    company = request.env['res.company'].sudo().search([], order='id asc', limit=1)
                    user_admin = request.env['res.users'].sudo().browse(user_id)

                    email_to = request.env['res.partner'].sudo().search(
                        [('email_remitentes', '=', True), ('email', '!=', False)]).mapped('email')
                    email_to = ",".join(email_to)
                    mail_values = {
                        'subject': "%s" % ('Reporte de Conciliacion'),
                        'email_from': user_admin.partner_id.email_formatted or 'admin@odoo.com',
                        'email_to': email_to,
                        'attachment_ids': [(6, 0, [data_id.id])],
                        'author_id': user_admin.partner_id.id,
                        'state': 'outgoing',
                    }
                    mail = request.env(user=user_id)['mail.mail'].sudo().create(mail_values)
                    mail.send(raise_exception=False)

                return vals
            else:
                mensaje_error = {
                    "Token": as_token,
                    "RespCode": -5,
                    "RespMessage": "Rechazado: Autenticación fallida"
                }
                return mensaje_error


        except Exception as e:
            mensaje_error = {
                "Token": as_token,
                "RespCode": -5,
                "RespMessage": "Rechazado: Autenticación fallida"
            }
            mensaje_error['RespMessage'] = f"Error: {str(e)}"
            return mensaje_error
