# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import re

class CustomsDeclaration(models.Model):
    _name = 'customs.declaration'
    _description = 'Declaration'
    
    def _compute_number_of_package(self):
        for rec in self:
            item_ids = self.env['customs.item'].search([('declaration_id', '=', rec.id)])
            no_of_item = len(item_ids)
            total_sum_package = 0
            for item_id in item_ids:
                no_of_package = 0
                for pac_line in item_id.package_line:
                    no_of_package += pac_line.no_of_package
                total_sum_package += no_of_package
            rec.number_of_item = no_of_item  
            rec.number_of_package = total_sum_package
    
    name = fields.Char(string="Transaction Ref.", required=True)
    consignor_id = fields.Many2one('res.partner', string="Consignor")
    consignee_id = fields.Many2one('res.partner', string="Consignee")
    
    incoterm_id = fields.Many2one('customs.incoterm', string="Incoterm")
    show_shipping_cost = fields.Boolean(related='incoterm_id.show_shipping_cost', string='Visible Shipping Cost')
    goods_port = fields.Selection(selection=[('yes', 'Yes'),
                                           ('no', 'No')], default='no', string='Are the goods at the port?')
    
    invoice_cost = fields.Float(string="Invoice Cost")
    invoice_currency_id = fields.Many2one('res.currency', string="Currency")
    shipping_cost = fields.Float(string="Shipping Cost")
    shipping_currency_id = fields.Many2one('res.currency', string="Currency")
    
    transport_mode_id = fields.Many2one('customs.transport.mode', string="Transport Mode")
    transport_mode_border_id = fields.Many2one('customs.transport.mode', string="Transport Mode at Border")
    
    transport_mode_border = fields.Selection(selection=[('sea', 'Sea'),
                                                       ('rail', 'Rail'),
                                                       ('road', 'Road'),
                                                       ('air', 'Air'),
                                                       ('roll_on_roll_off', 'Roll on Roll off')], string='Transport Mode at Border')
    
    uk_port = fields.Selection(selection=[('dov', 'DOV-Dover'),
                                           ('imm', 'IMM-Immingham'),
                                           ('lhr', 'LHR-London Heathrow')], string='UK Port')
    
    state = fields.Selection(selection=[('new', 'New'),
                                        ('draft', 'Draft'),
                                        ('post', 'Posted'),
                                        ('sent', 'Sent')], default='new', string='State')
    
    ducr = fields.Char(string="DUCR")
    number_of_item = fields.Integer(string="Number of Item", compute='_compute_number_of_package')
    number_of_package = fields.Integer(string="Number of Package", compute='_compute_number_of_package')
    dec_type = fields.Char(string="Declaration Type")
    
    
    
    @api.constrains('name')
    def _check_name_string(self):
        for rec in self:
            if rec.name:
                string = rec.name
                if re.match("^[a-zA-Z1-9_]*$", string):
                    return
                else:
                    raise UserError(_("Please only use numbers and letters."))
    
    def action_post(self):
        for dec in self:
            self.write({'state': 'post'})
            
    def action_send_email(self):
        for dec in self:
            self.write({'state': 'sent'})
            
    @api.model
    def create(self, vals):
        res = super(CustomsDeclaration, self).create(vals)
        if res.state == 'new':
            res.state = 'draft'
        
        last_year_number = ''
        year = datetime.now().year
        year = str(year)
        last_year_number = year[-1:]
        
        if not res.consignor_id.tid:
            raise UserError(_("There is no set TID for consignor %s !!\n Please Click setting and see in dropdown there is consignor menu set there TID in your consignor !!") % (res.consignor_id.name))    
            
        if not res.consignee_id.tid:
            raise UserError(_("There is no set TID for consignee %s !!\n Please Click setting and see in dropdown there is consignee menu set there TID in your consignee !!") % (res.consignee_id.name))
            
        if res.name and res.consignor_id and res.consignor_id.country_id.code == 'GB' and res.consignee_id and res.consignee_id.country_id.code == 'GB':
            res.ducr = last_year_number + res.consignor_id.tid + res.consignee_id.tid + '-' + res.name 
            
        if res.name and res.consignor_id and res.consignor_id.country_id.code == 'GB' and res.consignee_id and not res.consignee_id.country_id.code == 'GB':
            res.ducr = last_year_number + res.consignor_id.tid + '-' + res.name 
            
        if res.name and res.consignor_id and not res.consignor_id.country_id.code == 'GB' and res.consignee_id and res.consignee_id.country_id.code == 'GB':
            res.ducr = last_year_number  + res.consignee_id.tid + '-' + res.name 
            
        if res.name and res.consignor_id and not res.consignor_id.country_id.code == 'GB' and res.consignee_id and not res.consignee_id.country_id.code == 'GB':
            res.ducr = last_year_number + '-' + res.name 
        
        if res.consignee_id and res.consignee_id.country_id.code == 'GB':
            res.dec_type = 'IM' 
        else:
            res.dec_type = 'EX'
            
        if res.goods_port == 'yes':
            res.dec_type += 'A' 
        if res.goods_port == 'no':
            res.dec_type += 'D'
            
        return res
    
    @api.onchange('goods_port','consignee_id')
    def onchange_goods_port(self):
        for res in self:
            if res.consignee_id and res.consignee_id.country_id.code == 'GB':
                res.dec_type = 'IM' 
                
            if res.consignee_id and not res.consignee_id.country_id.code == 'GB':
                res.dec_type = 'EX'
                
            if res.consignee_id and res.goods_port == 'yes':
                res.dec_type += 'A' 
            if res.consignee_id and res.goods_port == 'no':
                res.dec_type += 'D'
        
            
        
                                        
    
    

