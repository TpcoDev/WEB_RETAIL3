from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'


    email_remitentes = fields.Boolean(default=False)