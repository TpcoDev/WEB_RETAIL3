# -*- coding: utf-8 -*-

import uuid
from odoo import http
from odoo.http import request, Response
import jsonschema
from jsonschema import validate
import json
import datetime


class TransferenciaAutomaticaController(http.Controller):

    @http.route('/tpco/odoo/ws007', auth="public", type="json", method=['POST'], csrf=False)
    def lista_ubicaciones(self, **post):

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
            request.uid = user_id
            if user_id:
                res['token'] = as_token

                stock_picking = request.env['stock.picking']
                stock_picking_type = request.env['stock.picking.type']
                production_lot = request.env['stock.production.lot']
                stock_move = request.env['stock.move']
                stock_quant = request.env['stock.quant']

                stock_picking_type_obj = stock_picking_type.sudo().search([('sequence_code', '=', 'INT')], limit=1)
                location_parent_id = request.env['stock.location'].search(
                    [('name', '=', post['params']['ubicacionPadre'])], limit=1)
                location_id = request.env['stock.location'].sudo().search([('name', '=', post['params']['ubicacion'])],
                                                                          limit=1)
                detalleActivos = []
                for detalle in post['params']['detalleActivos']:
                    production_lot_obj = production_lot.sudo().search([('name', '=', detalle['EPCCode'])], limit=1)
                    obj_stock_quant = stock_quant.sudo().search([('lot_id', '=', production_lot_obj.id)], limit=1)
                    if production_lot_obj:
                        producto_id = production_lot_obj.product_id
                        stock_picking_nuevo = stock_picking.sudo().create({
                            'product_id': producto_id.id,
                            'picking_type_id': stock_picking_type_obj.id,
                            'location_id': location_parent_id.id,
                            'location_dest_id': location_id.id,
                        })
                        # request.env.cr.commit()
                        stock_move.create({
                            'picking_id': stock_picking_nuevo.id,
                            'name': producto_id.name,
                            'product_id': producto_id.id,
                            'description_picking': producto_id.name,
                            'quantity_done': 1,
                            'lot_ids': [(production_lot_obj.id)],
                            'product_uom': 1,
                            'location_id': obj_stock_quant.location_id.id,
                            'location_dest_id': location_id.id,
                            'date': datetime.datetime.now(),
                            'company_id': 1,
                            'product_uom_qty': 1,
                        })
                        # request.env.cr.commit()
                        stock_picking_nuevo.action_confirm()
                        stock_picking_nuevo.button_validate()

                        detalleActivos.append({
                            "EPCCode": detalle['EPCCode'],
                            "codigo": 0,
                            "mensaje": "Activo transferido"
                        })
                    else:
                        detalleActivos.append({
                            "EPCCode": detalle['EPCCode'],
                            "codigo": 0,
                            "mensaje": "No se pudo transferir, Activo no esta en el sistema"
                        })

                return {
                    "idTransferencia": stock_picking_nuevo.id,
                    "fechaOperacion": datetime.datetime.now(),
                    "ubicacionPadre": location_parent_id.name,
                    "ubicacion": location_id.name,
                    "user": post['params']['user'],
                    "detalleActivos": detalleActivos
                }
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
