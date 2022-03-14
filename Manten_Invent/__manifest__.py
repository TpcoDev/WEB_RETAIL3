# -*- coding: utf-8 -*-
{
    'name': "Mantenimiento-Inventario",
    'description': """
           """,

    'author': "TPCO",
    'website': "http://www.tpco.com",
    'version': '14.20210208.2',

    # any module necessary for this one to work correctly

    'depends': ['maintenance'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/mantenimiento_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
