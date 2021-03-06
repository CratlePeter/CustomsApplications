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
    consignor_id = fields.Many2one('res.partner', string="Consignor", domain="[('is_company','=',True)]")
    consignee_id = fields.Many2one('res.partner', string="Consignee", domain="[('is_company','=',True)]")
    
    incoterm_id = fields.Many2one('customs.incoterm', string="Incoterm", required=True)
    show_shipping_cost = fields.Boolean(related='incoterm_id.show_shipping_cost', string='Visible Shipping Cost')
    goods_port = fields.Selection(selection=[('yes', 'Yes'),
                                           ('no', 'No')], default='no', string='Are the goods at the port?',
                                            required=True)
    
    invoice_cost = fields.Float(string="Invoice Cost for all items", required=True)
    invoice_currency_id = fields.Many2one('res.currency', string="Invoice Currency")
    shipping_cost = fields.Float(string="Shipping Cost")
    shipping_currency_id = fields.Many2one('res.currency', string="Shipping Cost Currency")
    
    transport_mode_id = fields.Many2one('customs.transport.mode', string="How are goods getting to the border?", required=True)
    transport_mode_border_id = fields.Many2one('customs.transport.mode', string="How are the goods getting over the border?", required=True)

    uk_port = fields.Many2one('customs.port', string='UK Port', required=True)
    
    state = fields.Selection(selection=[('new', 'New'),
                                        ('draft', 'Draft'),
                                        ('post', 'Committed'),
                                        ('sent', 'Sent')], default='new', string='State')
    
    ducr = fields.Char(string="DUCR")
    number_of_item = fields.Integer(string="Number of Item", compute='_compute_number_of_package')
    number_of_package = fields.Integer(string="Number of Package", compute='_compute_number_of_package')
    dec_type = fields.Char(string="Declaration Type")
    show_import_fields = fields.Boolean(string="Show fields applicable for import", default=False)
    
    @api.constrains('name')
    def _check_name_string(self):
        for rec in self:
            if rec.name:
                string = rec.name
                if re.match("^[a-zA-Z1-9_]*$", string):
                    return
                else:
                    raise UserError(_("Please only use numbers and letters."))

    def action_create_item(self):
        view_id = self.env.ref('cratle_customs.item_item_view_form').id
        return  {
            'name':'item_item_view_form',
            'res_model':'customs.item',
            'type':'ir.actions.act_window',
            'view_type':'form',
            'view_mode':'form',
            'view_id':view_id,
            'context': {'default_declaration_id': self.id},
            'target':'new',
        }


    def action_post(self):
        self._compute_number_of_package()
        if self.number_of_item > 0:
            self.write({'state': 'post'})
        else:
            raise UserError(_("There are no goods details attached to the header."))

    def action_rollback_to_draft(self):
        for dec in self:
            self.write({'state': 'draft'})
            
    def action_send_email(self):
        item_line_pattern = re.compile(r"(--.*--)")
        template_id = self.env.ref('cratle_customs.email_template_customs_declaration').id
        template = self.env['mail.template'].browse(template_id)

        for dec in self:
            if template:
                body = template.body_html
                try:
                    item_line = item_line_pattern.search(body).group(0)
                except AttributeError:
                    return
                body = ''
                if item_line:
                    updated_item_line = item_line.replace('--ducr--', dec.ducr)
                    updated_item_line = updated_item_line.replace('--port--', 'GB'+dec.uk_port.code)
                    item_ids = self.env['customs.item'].search([('declaration_id', '=', dec.name)])
                    item_number = 1
                    for item_id in item_ids:
                        updated_item_line = updated_item_line.replace('--item--', str(item_number))
                        updated_item_line = updated_item_line.replace('--cpc--', item_id.cp_code.code)
                        updated_item_line = updated_item_line.replace('--commodity_code--', item_id.comodity_code)
                        updated_item_line = updated_item_line.replace('--goods_description--',
                                                                      item_id.goods_description)
                        updated_item_line = updated_item_line.replace('--item_cost--', str(item_id.item_cost))
                        updated_item_line = updated_item_line.replace('--currency_id--', item_id.currency_id.name)
                        if item_id.valuation_method:
                            updated_item_line = updated_item_line.replace('--valuation_method--', item_id.valuation_method)
                        updated_item_line = updated_item_line.replace('--net_mass--', str(item_id.net_mass))
                        if item_id.country_of_origin:
                            updated_item_line = updated_item_line.replace('--country_of_origin--',
                                                                      item_id.country_of_origin.code)
                        if item_id.preference_code:
                            updated_item_line = updated_item_line.replace('--preference_code--',
                                                                          item_id.preference_code.code)
                        # AI Codes
                        sub_item_iterator = 0
                        for aicode in item_id.ai_statement_line:
                            if sub_item_iterator > 1:
                                break
                            updated_item_line = updated_item_line.replace('--ai_%s--' % str(sub_item_iterator),
                                                                          str(aicode.ai_code))
                            updated_item_line = updated_item_line.replace('--ai_text_%s--' % str(sub_item_iterator),
                                                                          str(aicode.associated_value))
                            sub_item_iterator += 1
                        # Document codes
                        sub_item_iterator = 0
                        for doco in item_id.document_code_line:
                            if sub_item_iterator > 1:
                                break
                            updated_item_line = updated_item_line.replace('--doc_code_%s--' % str(sub_item_iterator),
                                                                            doco.name.code)
                            updated_item_line = updated_item_line.replace('--doc_ref_%s--' % str(sub_item_iterator),
                                                                            doco.document_ref)
                            updated_item_line = updated_item_line.replace('--doc_status_%s--' % str(sub_item_iterator),
                                                                            doco.document_status.code)
                            sub_item_iterator += 1
                        # Previous document
                        sub_item_iterator = 0
                        for pdoco in item_id.previous_document_line:
                            if sub_item_iterator > 2:
                                break
                            updated_item_line = updated_item_line.replace(
                                '--prev_doc_code_%s--' % str(sub_item_iterator),
                                pdoco.document_type.code)
                            updated_item_line = updated_item_line.replace(
                                '--prev_doc_ref_%s--' % str(sub_item_iterator),
                                pdoco.doc_reference)
                            sub_item_iterator += 1
                        # Package lines
                        sub_item_iterator = 0
                        for pline in item_id.package_line:
                            if sub_item_iterator > 2:
                                break
                            updated_item_line = updated_item_line.replace(
                                '--num_packages_%s--' % str(sub_item_iterator), str(pline.no_of_package))
                            updated_item_line = updated_item_line.replace(
                                '--package_type_%s--' % str(sub_item_iterator), pline.box_type_id.code)
                            updated_item_line = updated_item_line.replace(
                                '--package_marks_%s--' % str(sub_item_iterator), pline.package_mark)
                            sub_item_iterator += 1
                        # Containers
                        sub_item_iterator = 0
                        for container in item_id.container_line:
                            if sub_item_iterator > 2:
                                break
                            updated_item_line = updated_item_line.replace('--container_%s--' % str(sub_item_iterator),
                                                                          container.name)
                            sub_item_iterator += 1
                        # Consignor
                        updated_item_line = updated_item_line.replace('--nor_company name--', dec.consignor_id.name)
                        updated_item_line = updated_item_line.replace('--nor_tid--', dec.consignor_id.tid)
                        if dec.consignor_id.street:
                            updated_item_line = updated_item_line.replace('--nor_address 1--', dec.consignor_id.street)
                        if dec.consignor_id.street2:
                            updated_item_line = updated_item_line.replace('--nor_address 2--', dec.consignor_id.street2)
                        if dec.consignor_id.zip:
                            updated_item_line = updated_item_line.replace('--nor_postcode--', dec.consignor_id.zip)
                        if dec.consignor_id.country_id:
                            updated_item_line = updated_item_line.replace('--nor_country--',
                                                                          dec.consignor_id.country_id.code)
                        # Consignee
                        updated_item_line = updated_item_line.replace('--nee_company name--', dec.consignee_id.name)
                        updated_item_line = updated_item_line.replace('--nee_tid--', dec.consignee_id.tid)
                        if dec.consignee_id.street:
                            updated_item_line = updated_item_line.replace('--nee_address 1--', dec.consignee_id.street)
                        if dec.consignee_id.street2:
                            updated_item_line = updated_item_line.replace('--nee_address 2--', dec.consignee_id.street2)
                        if dec.consignee_id.zip:
                            updated_item_line = updated_item_line.replace('--nee_postcode--', dec.consignee_id.zip)
                        if dec.consignee_id.country_id:
                            updated_item_line = updated_item_line.replace('--nee_country--',
                                                                          dec.consignee_id.country_id.code)

                        # Update item to Sent state
                        item_id.update_to_sent()

                        # Loop management
                        item_number += 1
                        body += updated_item_line
                    # Set up the metadata for the mail
                    mail_values = {
                         'body_html': body,
                    }
                    # Send the email
                    template.send_mail(self.id, force_send=True, email_values=mail_values)
                    self.write({'state': 'sent'})
                else:
                    raise UserError(_("Please check the email template follows the correct format."))
            else:
                raise UserError(_("Please check the that this email template is loaded: %s" % template_title))
            
    @api.model
    def create(self, vals):
        res = super(CustomsDeclaration, self).create(vals)
        if res.state == 'new':
            res.state = 'draft'
        
        last_year_number = ''
        year = str(datetime.now().year)
        last_year_number = year[-1:]
        
        if not res.consignor_id.tid:
            raise UserError(_("There is no set TID for consignor %s.\nPlease the TID to be the company EORI.  If no EORI is available then create your own reference.") % (res.consignor_id.name))
            
        if not res.consignee_id.tid:
            raise UserError(_("There is no set TID for consignee %s.\nPlease the TID to be the company EORI.  If no EORI is available then create your own reference.") % (res.consignee_id.name))
            
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
        else:
            res.dec_type += 'D'
            
        return res
    
    @api.onchange('goods_port','consignee_id','consignor_id')
    def onchange_goods_port(self):
        for res in self:

            if res.consignee_id and res.consignee_id.country_id.code == 'GB':
                res.dec_type = 'IM'
                res.show_import_fields = True
            else:
                res.dec_type = 'EX'
                res.show_import_fields = False
                
            if res.consignee_id and res.goods_port == 'yes':
                res.dec_type += 'A' 
            if res.consignee_id and res.goods_port == 'no':
                res.dec_type += 'D'