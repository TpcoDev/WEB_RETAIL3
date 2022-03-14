from odoo import api, fields, models, _


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    @api.onchange('stock_production_lot_id')
    def _product_change(self):
        self.name = self.stock_production_lot_id.product_id.name
        if self.stock_production_lot_id.product_id.categ_id.name:
            categ_producto_obj = self.env['maintenance.equipment.category'].search([('name', '=', self.stock_production_lot_id.product_id.categ_id.name)])
            if categ_producto_obj:
               self.category_id = categ_producto_obj.id
            else:
                categ_mantenimiento_obj =self.env['maintenance.equipment.category'].create({'name':self.stock_production_lot_id.product_id.categ_id.name})
                self.category_id = categ_mantenimiento_obj.id

        self.partner_ref = self.stock_production_lot_id.product_id.default_code
        self.serial_no =self.stock_production_lot_id.name
        self.effective_date =self.stock_production_lot_id.create_date
        stock_quant_obj = self.env['stock.quant'].search([('lot_id','=',self.stock_production_lot_id.id)])
        if stock_quant_obj:
            if len(stock_quant_obj)>1:
                self.location = stock_quant_obj.location_id[1].complete_name
            else:
                self.location = stock_quant_obj.location_id[0].complete_name
        self.technician_user_id =self.env.user.id


    stock_production_lot_id = fields.Many2one('stock.production.lot', string='Producto', required=True)
    creado = fields.Boolean()

    @api.model_create_multi
    def create(self, vals_list):
        vals_list[0]['creado'] = True
        maintenance = super(MaintenanceEquipment, self).create(vals_list)
        return maintenance



