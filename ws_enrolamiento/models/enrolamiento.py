from odoo import api, fields, models, _


class ProductoEnrolamiento(models.Model):
    _inherit = 'product.template'

    imagen = fields.Image('Imagen')
    tipo_prenda_id = fields.Many2one('tipo.prenda', 'Tipo de prenda')
    marca_id = fields.Many2one('marca', 'Marca')
    tamanno_id = fields.Many2one('tamanno', 'Tamaño')
    origen_id = fields.Many2one('origen', 'Origen')
    color_id = fields.Many2one('color', 'Color')
    genero_id = fields.Many2one('genero', 'Género')
    idHandheld = fields.Char('Handheld')


class TipoPrenda(models.Model):
    _name = "tipo.prenda"

    name = fields.Char(string='Nombre', required=True)


class Marca(models.Model):
    _name = "marca"

    name = fields.Char(string='Nombre', required=True)


class Tamanno(models.Model):
    _name = "tamanno"

    name = fields.Char(string='Nombre', required=True)


class Origen(models.Model):
    _name = "origen"

    name = fields.Char(string='Nombre', required=True)


class Color(models.Model):
    _name = "color"

    name = fields.Char(string='Nombre', required=True)


class Genero(models.Model):
    _name = "genero"

    name = fields.Char(string='Nombre', required=True)
