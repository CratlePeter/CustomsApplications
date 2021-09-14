# -*- coding: utf-8 -*-

{
    'name'       : 'Declaration Record',
    'author'     : 'Cratle Limited',
    'version'    : '0.1',
    'category'   : 'Operations/Customs',
    'summary'    : 'Manage declaration emails and records',
    'website'    : 'http://customs.cratle.co.uk', 
    'email'      : 'contact@cratle.co.uk',
    'maintainer' : "ERPcaLL Solutions",
    'description': """
    Manage the records of declarations and the inbound emails from CSPs.
""",
    
    'depends'    : ['base','contacts'],
    
    'data'       : [
                    'security/ir.model.access.csv',
                    'views/declaration_record_views.xml',
                    'views/ir_cron_data.xml',
                    'views/menu_views.xml',
                   ],
    
    'demo'       : [
                   ],
    
    'installable': True,
    'auto_install': False,
    'application': True,
}
