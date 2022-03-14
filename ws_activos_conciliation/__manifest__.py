# -*- coding: utf-8 -*-
{
    'name': "WS Conciliation Activos",
    'description': """
           """,

    'author': "TPCO",
    'website': "http://www.tpco.com",
    'version': '14.20220310',

    # any module necessary for this one to work correctly

    'depends': ['contacts','stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'report/reports_views.xml',
        'views/res_partner_views.xml',

    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}
