# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _

class CustomsItem(models.Model):
    _name = 'customs.item'
    rec_name = 'declaration_id'
    _description = 'Item'
    
    declaration_id = fields.Many2one('customs.declaration', string="Related Header", required=True)
    ducr_code = fields.Char(string="Custom Procedure",)
    comodity_code = fields.Char(string="Commodity Code")
    goods_description = fields.Char(string="Goods Description")
    item_cost = fields.Float(string="Item Cost")
    currency_id = fields.Many2one('res.currency', string="Currency")
    valuation_method = fields.Selection(selection=[('inv_value', 'Invoice Value'),
                                                   ('transaction_value_ig', 'Transaction value of identical goods'),
                                                   ('transaction_value_sg', 'Transaction value of similar goods'),
                                                   ('deductive_method', 'The Deductive Method')], string='Valuation Method')
    net_mass = fields.Float(string="Net Mass(kg)")
    
    state = fields.Selection(selection=[('new', 'New'),
                                        ('draft', 'Draft'),
                                        ('attach', 'Attach to Header'),
                                        ('lock', 'Locked'),
                                        ('sent', 'Sent')], default='new', string='State')
    
    package_line = fields.One2many('package.line', 'package_id', string='Package Lines')
    ai_statement_line = fields.One2many('ai.statement.line', 'ai_statement_id', string='AI Statement Lines')
    document_code_line = fields.One2many('document.code.line', 'document_code_id', string='Document Code Lines')
    previous_document_line = fields.One2many('previous.document.line', 'previous_document_id', string='Previous Document Lines')
    container_line = fields.One2many('container.line', 'container_id', string='Container Lines')
    
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
    _name = 'container.line'
    _description = 'Container Line'
    
    container_id = fields.Many2one('customs.item', string="Item")
    name = fields.Char(string="Reference", required=True)
    
class PreviousDocumentLine(models.Model):
    _name = 'previous.document.line'
    _description = 'Previous Document Line'
    
    previous_document_id = fields.Many2one('customs.item', string="Item")
    document_type = fields.Many2one('customs.previous.document', string='Document Type', required=True)
    doc_value = fields.Char(string="Document Reference")
    
class DocumentCodeLine(models.Model):
    _name = 'document.code.line'
    _description = 'Document Code Line'
    
    document_code_id = fields.Many2one('customs.item', string="Item")
    name = fields.Many2one('customs.document.code', string="Code")
    document_ref = fields.Char(string="Document")
    document_status = fields.Char(string="Document Status")
    
class AiStatement(models.Model):
    _name = 'ai.statement.line'
    _description = 'AI Statements Line'
    
    ai_statement_id = fields.Many2one('customs.item', string="Item")
    box_type_id = fields.Many2one('customs.addinfocodes', string="Statements", required=True)
    associated_value = fields.Char(string="Value")
    
class PackageLine(models.Model):
    _name = 'package.line'
    _description = 'Package Line'
    
    package_id = fields.Many2one('customs.item', string="Item")
    no_of_package = fields.Integer(string="Number of Packages")
    package_mark = fields.Char(string='Package Marks')
    box_type_id = fields.Many2one('customs.box.type', string="Package Type",required=True)

   
    
    

