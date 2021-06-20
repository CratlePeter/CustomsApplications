# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError

class CustomsItem(models.Model):
    _name = 'customs.item'
    _rec_name = 'declaration_id'
    _description = 'Item'

    declaration_id = fields.Many2one('customs.declaration', string="Related Header",
                                     domain="[('state','=','draft')]")
    dec_type = fields.Char(string="Declaration Type")
    cp_code = fields.Many2one('customs.procedure', string="Custom Procedure",
                              domain="[('type','=',dec_type)]",
                              required=True)
    comodity_code = fields.Char(string="Commodity Code", required=True)
    goods_description = fields.Char(string="Goods Description", required=True)
    country_of_origin = fields.Many2one('res.country', string="Country of origin")
    preference_code = fields.Many2one('customs.preference.code', string="Preference Code")
    item_cost = fields.Float(string="Item Cost", required=True)
    currency_id = fields.Many2one('res.currency', string="Valuation currency", required=True)
    valuation_method = fields.Selection(selection=[('1', 'Invoice Value'),
                                                   ('2', 'Transaction value of identical goods'),
                                                   ('3', 'Transaction value of similar goods'),
                                                   ('4', 'Deductive Method'),
                                                   ('5', 'Computed Value'),
                                                   ('6', 'Fallback method')], string='Valuation Method')
    net_mass = fields.Float(string="Net Mass(kg)", required=True)
    
    state = fields.Selection(selection=[('new', 'New'),
                                        ('draft', 'Draft'),
                                        ('attach', 'Attached to Header'),
                                        ('lock', 'Locked'),
                                        ('sent', 'Sent')], default='new', string='State')
    
    package_line = fields.One2many('customs.item.package.line', 'package_id', string='Package Lines')
    ai_statement_line = fields.One2many('customs.item.ai.statement.line', 'ai_statement_id', string='AI Statement Lines')
    document_code_line = fields.One2many('customs.item.document.code.line', 'document_code_id', string='Document Code Lines')
    previous_document_line = fields.One2many('customs.item.previous.document.line', 'previous_document_id', string='Previous Document Lines')
    container_line = fields.One2many('customs.item.container.line', 'container_id', string='Container Lines')
    
    def action_lock(self):
        self.write({'state': 'lock'})

    def update_to_sent(self):
        self.write({'state': 'sent'})

    def action_rollback_to_draft(self):
        self.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        res = super(CustomsItem, self).create(vals)
        if res.state == 'new':
            res.state = 'attach'

        # Entry error checking
        if res.dec_type == 'I':
            if len(res.comodity_code) < 10:
                raise UserError(_('You must use at least 10 characters (usually 10) for the commodity code.'))
            if not res.country_of_origin:
                raise UserError(_('You must enter the economic origin of the goods.'))
            if not res.preference_code:
                raise UserError(_(
                    'You must enter the preference code for the goods.\nUsually 100-no preference or 30x for EU preference'))
            if not res.valuation_method:
                raise UserError(_('You must show how you valued the goods.'))
        else:
            if len(res.comodity_code) < 8:
                raise UserError(_('You must use at least 8 characters for the commodity code.'))
        if not res.comodity_code.isnumeric():
            raise UserError(_('The commodity code must be numeric without spaces.'))
        if not res.item_cost or res.item_cost <= 0:
            raise UserError(_('Please set the invoice cost for the item.'))
        if not res.currency_id:
            raise UserError(_('Please set the currency used to value the item'))
        if not res.net_mass or res.net_mass <= 0:
            raise UserError(_('Please set the net mass of the item'))

        return res


    @api.onchange('declaration_id','cp_code')
    def onchange_declaration_setup_type (self):
        for dec in self.declaration_id:
            self.dec_type = dec.dec_type[:1]
    
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
    doc_reference = fields.Char(string="Document Reference", required=True)
    
class DocumentCodeLine(models.Model):
    _name = 'customs.item.document.code.line'
    _description = 'Document Code Line'
    
    document_code_id = fields.Many2one('customs.item', string="Item", required=True)
    name = fields.Many2one('customs.document.code', string="Name", required=True)
    document_ref = fields.Char(string="Document")
    document_status = fields.Many2one('customs.document.status', string="Status", required=True)
    
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
    no_of_package = fields.Integer(string="Number of Packages", required=True)
    box_type_id = fields.Many2one('customs.box.type', string="Package Type", required=True)
    package_mark = fields.Char(string='Package Marks', required=True)
