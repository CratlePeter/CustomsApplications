# -*- coding: utf-8 -*-

{
    'name'       : 'Cratle Customs Declarations',
    'author'     : 'Cratle Limited',
    'version'    : '13.0.0.1',
    'category'   : 'Operations/Customs',
    'summary'    : 'Declare items to UK customs',
    'website'    : 'http://customs.cratle.co.uk', 
    'email'      : 'contact@cratle.co.uk',
    'price'      : 70,
    'currency'   : 'EUR',
    'maintainer' : "ERPcaLL Solutions",
    'description': """
    Declare imports and exports to UK customs through the Cratle customs broker.
        This Odoo module is a front-end to the Cratle declarations server.  If this is not installed then the module will email declarations for processing.
""",
    
    'depends'    : ['mail','contacts','base',],
    
    'data'       : [
                    'security/security_group.xml',
                    'security/ir.model.access.csv',
                    'data/customs.addinfocodes.csv',
                    'data/customs.transport.mode.csv',
                    'data/customs.incoterm.csv',
                    'data/customs.document.code.csv',
                    'data/customs.box.type.csv',
                    'data/customs.previous.document.csv',
                    'data/customs.procedure.csv',
                    'data/customs.port.csv',
                    'data/customs.document.status.csv',
                    'data/customs.preference.code.csv',
                    'data/email_template.xml',
                    'views/master_views.xml',
                    'views/res_partner_views.xml',
                    'views/declaration_views.xml',
                    'views/item_views.xml',
                    'views/menu_views.xml',
                   ],
    
    'demo'       : [
                   ],
    'images'     : [
                    'static/description/banner.png',
                    'static/description/icon.png',
                    'static/description/favicon.png',
                   ],
    
    'installable': True,
    'auto_install': False,
    'application': True,
    'licence': 'AGPL-3'  
}
