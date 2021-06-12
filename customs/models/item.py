# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _

class CustomsItem(models.Model):
    _name = 'customs.item'
    rec_name = 'declaration_id'
    _description = 'Item'
    
    declaration_id = fields.Many2one('customs.declaration', string="Related Header", required=True)
    cp_code = fields.Many2one('customs.procedure', string="Custom Procedure", required=True)
    comodity_code = fields.Char(string="Commodity Code")
    goods_description = fields.Char(string="Goods Description")
    country_of_origin = fields.Many2one('res.country', string="Country of origin", required=True)
    preference_code = fields.Many2one('customs.preference.code', string="Preference Code", required=True)
    item_cost = fields.Float(string="Item Cost")
    currency_id = fields.Many2one('res.currency', string="Currency")
    valuation_method = fields.Selection(selection=[('1', 'Invoice Value'),
                                                   ('2', 'Transaction value of identical goods'),
                                                   ('3', 'Transaction value of similar goods'),
                                                   ('4', 'Deductive Method'),
                                                   ('5', 'Computed Value'),
                                                   ('6', 'Fallback method')], string='Valuation Method')
    net_mass = fields.Float(string="Net Mass(kg)")
    
    state = fields.Selection(selection=[('new', 'New'),
                                        ('draft', 'Draft'),
                                        ('attach', 'Attach to Header'),
                                        ('lock', 'Locked'),
                                        ('sent', 'Sent')], default='new', string='State')
    
    package_line = fields.One2many('customs.item.package.line', 'package_id', string='Package Lines')
    ai_statement_line = fields.One2many('customs.item.ai.statement.line', 'ai_statement_id', string='AI Statement Lines')
    document_code_line = fields.One2many('customs.item.document.code.line', 'document_code_id', string='Document Code Lines')
    previous_document_line = fields.One2many('customs.item.previous.document.line', 'previous_document_id', string='Previous Document Lines')
    container_line = fields.One2many('customs.item.container.line', 'container_id', string='Container Lines')
    
    def action_lock(self):
        for item in self:
            self.write({'state': 'lock'})
    
    @api.model
    def create(self, vals):
        res = super(CustomsItem, self).create(vals)
        if res.state == 'new':
            res.state = 'draft'
        return res
    
class ContainerLine(models.Model):
    _name = 'customs.item.container.line'
    _description = 'Container Line'
    
    container_id = fields.Many2one('customs.item', string="Item")
    name = fields.Char(string="Reference", required=True)
    
class PreviousDocumentLine(models.Model):
    _name = 'customs.item.previous.document.line'
    _description = 'Previous Document Line'
    
    previous_document_id = fields.Many2one('customs.item', string="Item")
    document_type = fields.Many2one('customs.previous.document', string='Document Type', required=True)
    doc_reference = fields.Char(string="Document Reference")
    
class DocumentCodeLine(models.Model):
    _name = 'customs.item.document.code.line'
    _description = 'Document Code Line'
    
    document_code_id = fields.Many2one('customs.item', string="Item")
    name = fields.Many2one('customs.document.code', string="Name")
    document_ref = fields.Char(string="Document")
    document_status = fields.Many2one('customs.document.status', string="Description")
    
class AiStatement(models.Model):
    _name = 'customs.item.ai.statement.line'
    _description = 'AI Statements Line'
    
    ai_statement_id = fields.Many2one('customs.item', string="Item")
    ai_code = fields.Many2one('customs.addinfocodes', string="Statements", required=True)
    associated_value = fields.Char(string="Value")
    
class PackageLine(models.Model):
    _name = 'customs.item.package.line'
    _description = 'Package Line'
    
    package_id = fields.Many2one('customs.item', string="Item")
    no_of_package = fields.Integer(string="Number of Packages")
    package_mark = fields.Char(string='Package Marks')
    box_type_id = fields.Many2one('customs.box.type', string="Package Type",required=True)
