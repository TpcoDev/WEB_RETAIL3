# -*- coding: utf-8 -*-

import uuid
from odoo import http
from odoo.http import request, Response
import jsonschema
from jsonschema import validate
import json
import datetime


class EnrolamientoController(http.Controller):

    @http.route('/tpco/odoo/ws001', auth="public", type="json", method=['POST'], csrf=False)
    def enrolamiento(self, **post):

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
            "RespMessage": "Producto se agregó correctamente"
        }
        mensaje_error_existencia = {
            "Token": as_token,
            "RespCode": 1,
            "RespMessage": "Activo ya existe no se enrolará"
        }

        try:
            myapikey = request.httprequest.headers.get("Authorization")
            if not myapikey:
                # self.create_message_log("ws001", as_token, post, 'RECHAZADO', 'API KEY no existe')
                mensaje_error['RespCode'] = -2
                mensaje_error['RespMessage'] = f"Rechazado: API KEY no existe"
                return mensaje_error

            user_id = request.env["res.users.apikeys"]._check_credentials(scope="rpc", key=myapikey)
            request.uid = user_id
            if user_id:
                res['token'] = as_token

                product_tmpl = request.env['product.template']
                production_lot = request.env['stock.production.lot']
                tipo_prenda = request.env['tipo.prenda']
                marca = request.env['marca']
                tamanno = request.env['tamanno']
                origen = request.env['origen']
                color = request.env['color']
                genero = request.env['genero']

                location_parent_id = request.env['stock.location'].search(
                    [('name', '=', post['params']['ubicacionPadre'])], limit=1)
                location_id = request.env['stock.location'].sudo().search([('name', '=', post['params']['ubicacion'])],
                                                                          limit=1)

                if location_parent_id:
                    location_id = request.env['stock.location'].sudo().search(
                        [('name', '=', post['params']['ubicacion']), ('location_id', '=', location_parent_id.id)],
                        limit=1)

                for detalle in post['params']['detalleActivos']:
                    obj_tipo_prenda = tipo_prenda.sudo().search(
                        [('name', '=', detalle['tipoPrenda'])], limit=1)
                    if not obj_tipo_prenda:
                        obj_tipo_prenda = tipo_prenda.sudo().create(
                            {'name': detalle['tipoPrenda']})

                    obj_marca = marca.sudo().search([('name', '=', detalle['marca'])], limit=1)
                    if not obj_marca:
                        obj_marca = marca.sudo().create({'name': detalle['marca']})

                    obj_tamanno = tamanno.sudo().search(
                        [('name', '=', detalle['tamanno'])], limit=1)
                    if not obj_tamanno:
                        obj_tamanno = tamanno.sudo().create(
                            {'name': detalle['tamanno']})

                    obj_origen = origen.sudo().search(
                        [('name', '=', detalle['origen'])], limit=1)
                    if not obj_origen:
                        obj_origen = origen.sudo().create({'name': detalle['origen']})

                    obj_color = color.sudo().search([('name', '=', detalle['color'])], limit=1)
                    if not obj_color:
                        obj_color = color.sudo().create({'name': detalle['color']})

                    obj_genero = genero.sudo().search(
                        [('name', '=', detalle['genero'])], limit=1)
                    if not obj_genero:
                        obj_genero = genero.sudo().create({'name': detalle['genero']})

                    product_tmpl_nuevo = product_tmpl.search([('default_code', '=', detalle['SKU'])], limit=1)
                    if not product_tmpl_nuevo:

                        product_tmpl_nuevo = product_tmpl.sudo().create({
                            'name': detalle['nombreActivo'],
                            'default_code': detalle['SKU'],
                            'tipo_prenda_id': obj_tipo_prenda.id,
                            'marca_id': obj_marca.id,
                            'tamanno_id': obj_tamanno.id,
                            'origen_id': obj_origen.id,
                            'color_id': obj_color.id,
                            'genero_id': obj_genero.id,
                            'list_price': 1.00,
                            'standard_price': 0.00,
                            'use_expiration_date': False,
                            'tracking': 'serial',
                            'purchase_ok': True,
                            'sale_ok': True,
                            'type': 'product'

                        })
                        request.env.cr.commit()

                        for epc in detalle['DetalleEpc']:
                            production_lot_nuevo = production_lot.sudo().search([('name', '=', epc['EPCCode'])],
                                                                                limit=1)
                            if not production_lot_nuevo:
                                production_lot_nuevo = production_lot.sudo().create({
                                    'product_id': product_tmpl_nuevo.id,
                                    'name': epc['EPCCode'],
                                    'company_id': request.env.user.company_id.id,
                                })

                            else:
                                return mensaje_error_existencia

                            stock_move_nuevo = request.env['stock.move'].sudo().create({
                                'date': datetime.datetime.now(),
                                'name': 'Cantidad de producto actualizada',
                                'reference': 'Cantidad de producto actualizada',
                                'product_id': product_tmpl_nuevo.id,
                                'location_id': 14,
                                'location_dest_id': location_id.id,
                                'state': 'done',
                                'company_id': request.env.user.company_id.id,
                                'product_uom': 1,
                                'product_uom_qty': 1,
                            })
                            request.env.cr.commit()

                            request.env['stock.move.line'].sudo().create({
                               'date':datetime.datetime.now(),
                               'reference':'Cantidad de producto actualizada',
                               'product_id': product_tmpl_nuevo.id,
                               'lot_id': production_lot_nuevo.id,
                               'location_id': 14,
                               'location_dest_id': location_id.id,
                               'qty_done':1,
                               'state': 'done',
                               'company_id': request.env.user.company_id.id,
                               'product_uom_id': 1,
                               'move_id': stock_move_nuevo.id,
                               'reference': 'Inv. Adj.: Inventory'
                            })
                            request.env.cr.commit()

                        return mensaje_correcto



                    else:
                        product_tmpl_nuevo.write({
                            'name': detalle['nombreActivo'],
                            'tipo_prenda_id': obj_tipo_prenda.id,
                            'marca_id': obj_marca.id,
                            'tamanno_id': obj_tamanno.id,
                            'origen_id': obj_origen.id,
                            'color_id': obj_color.id,
                            'genero_id': obj_genero.id,
                            'list_price': 1.00,
                            'standard_price': 0.00,
                            'use_expiration_date': False,
                            'tracking': 'serial',
                            'purchase_ok': True,
                            'sale_ok': True,
                            'type': 'product'
                        })

                        for epc in detalle['DetalleEpc']:
                            production_lot_nuevo = production_lot.sudo().search([('name', '=', epc['EPCCode'])],
                                                                                limit=1)
                            if not production_lot_nuevo:
                                production_lot_nuevo = production_lot.sudo().create({
                                    'product_id': product_tmpl_nuevo.id,
                                    'name': epc['EPCCode'],
                                    'company_id': request.env.user.company_id.id,
                                })
                            else:
                                return mensaje_error_existencia

                            stock_move_nuevo = request.env['stock.move'].sudo().create({
                                'date': datetime.datetime.now(),
                                'name': 'Cantidad de producto actualizada',
                                'reference': 'Cantidad de producto actualizada',
                                'product_id': product_tmpl_nuevo.id,
                                'location_id': 14,
                                'location_dest_id': location_id.id,
                                'state': 'done',
                                'company_id': request.env.user.company_id.id,
                                'product_uom': 1,
                                'product_uom_qty': 1,
                            })
                            request.env.cr.commit()

                            request.env['stock.move.line'].sudo().create({
                                'date': datetime.datetime.now(),
                                'reference': 'Cantidad de producto actualizada',
                                'product_id': product_tmpl_nuevo.id,
                                'lot_id': production_lot_nuevo.id,
                                'location_id': 14,
                                'location_dest_id': location_id.id,
                                'qty_done': 1,
                                'state': 'done',
                                'company_id': request.env.user.company_id.id,
                                'product_uom_id': 1,
                                'move_id': stock_move_nuevo.id,
                                'reference': 'Inv. Adj.: Inventory'
                            })
                            request.env.cr.commit()

                        return mensaje_correcto



        except Exception as e:
            mensaje_error = {
                "Token": as_token,
                "RespCode": -5,
                "RespMessage": "Rechazado: Autenticación fallida"
            }
            mensaje_error['RespMessage'] = f"Error: {str(e)}"
            return mensaje_error
