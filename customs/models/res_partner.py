# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _

class Partner(models.Model):
    _inherit = 'res.partner'
    
    is_consignor = fields.Boolean(string="Is a Consignor")
    is_consignee = fields.Boolean(string="Is a Consignee")
    tid = fields.Char(string="TID")
