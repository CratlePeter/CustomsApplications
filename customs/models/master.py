# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _

class CustomsBoxType(models.Model):
    _name = 'customs.box.type'
    _description = 'Package Type'

    code = fields.Char(string="Code", required=True)
    name = fields.Char(string="Name", required=True)
    
class CustomsAddInfoCodes(models.Model):
    _name = 'customs.addinfocodes'
    _description = 'AI Codes'
    
    name = fields.Char(string="Name", required=True)
    
class CustomsIncoterm(models.Model):
    _name = 'customs.incoterm'
    _description = 'Incoterm'
    
    name = fields.Char(string="Name", required=True)
    show_shipping_cost = fields.Boolean(string='Visible Shipping Cost')
    
class CustomsTransportMode(models.Model):
    _name = 'customs.transport.mode'
    _description = 'Transport Mode'
    
    name = fields.Char(string="Name", required=True)
    
class CustomsDocumentCode(models.Model):
    _name = 'customs.document.code'
    _description = 'Document Code'
    
    code = fields.Char(string="Code", required=True)
    type_of_declaration = fields.Char(string="Import or Export", required=True)
    declaration_level = fields.Char(string="Used at Header or Item level", required=True)
    name = fields.Char(string="Name", required=True)
    details = fields.Char(string="Details for the code", required=True)

class CustomsPreviousDocument(models.Model):
    _name = 'customs.previous.document'
    _description = 'Previous documents about these goods'

    code = fields.Char(string="Code", required=True)
    name = fields.Char(string="Name", required=True)
