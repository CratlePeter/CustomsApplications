# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import logging
import re

_logger = logging.getLogger(__name__)

class DeclarationRecord(models.Model):
    _name = 'declaration.record'
    _inherit = ['mail.thread']
    _description = 'Declaration Record'

    type = fields.Selection(selection=[('import', 'Import'),
                                       ('export', 'Export'),
                                       ('transit', 'Transit'),], string='Type')

    name = fields.Char(string="DUCR")
    epu = fields.Char(string="EPU")
    entry_no = fields.Char(string="Entry No.")
    mrn = fields.Char(string="MRN")
    doe = fields.Date(string="DoE")
    ecd = fields.Date(string="Expected Crossing Date")
    requestor_id = fields.Many2one('res.partner', string="Requestor")
    response_id = fields.Many2one('mail.template', string="Response Email")
    cc_list = fields.Text(string="CC List")

    owner_id = fields.Many2one('res.partner', string="Owner")
    owner_mail_id = fields.Many2one('mail.template', string="Owner Email")
    owner_cc = fields.Text(string="Owner CC")

    border_crossing_id = fields.Many2one('mail.template', string="Border Crossing Email")


    attachment_ids = fields.Many2many('ir.attachment', 'declaration_rec_attachment_rel',
                                      'declaration_rec_attachment_id', 'attachment_declaration_rec_id',
                                      string='Attachments')
    internal_ref = fields.Char(string="Internal Ref.")
    their_reference = fields.Char(string="External Reference")

    message_line = fields.One2many('mail.message', 'declaration_email_message_id', string="History Line")

    def border_crossing_email(self):
        today = fields.Date.today()
        declaration_record_objs = self.env['declaration.record'].search([('ecd', '=', today)])

        for declaration_record_obj in declaration_record_objs:
            if declaration_record_obj.requestor_id:
                declaration_record_obj.send_email(declaration_record_obj.requestor_id,
                                                  declaration_record_obj.cc_list,
                                                  declaration_record_obj.border_crossing_id,
                                                  'Border Crossing')


    def send_email (self, party_to_send_to, cc_list, template_to_use, message_subtype):
        mail_values = template_to_use.generate_email(self.id)
        mail_values['attachment_ids'] = [(6, 0, self.attachment_ids.ids)]
        subtype = self.env['mail.message.subtype'].search([('name', '=', message_subtype)],
                                                                               limit=1)
        # Tidy up cc_list before adding it into the mail_values array
        if len(cc_list) > 0:
            cc_split = cc_list.split(';')
            if len(cc_split) == 1 and cc_list.find(',',2)>0:
                cc_split = cc_list.split(',')

            for i, cc in enumerate(cc_split):
                cc_split[i] = tools.email_normalize(cc)

            cc_list = ','.join(cc_split)
            mail_values['email_cc'] = cc_list


        # Create a message so that it's available in the history
        message_id = self.env['mail.message'].create({
            'message_type': 'email',
            'subtype_id': subtype.id,
            'model': self._name,
            'record_name': self.name,
            'res_id': self.id,
            'body': mail_values['body_html'],
            'subject': mail_values['subject'],
            'partner_ids': [(6, 0, party_to_send_to.ids)],
            'declaration_email_message_id': self.id,
        })

        # Create and queue the email for sending using the values from the mail.message
        mail_values['mail_message_id'] = message_id.id
        mail_id = self.env['mail.mail'].create(mail_values)

    def action_email_owner(self):
        if self.owner_id and self.owner_mail_id:
            #self.owner_mail_id.send_mail(self.id)
            self.send_email (self.owner_id, self.owner_cc, self.owner_mail_id, 'Owner')

    def action_email_requestor(self):
        if self.requestor_id and self.response_id:
            self.send_email (self.requestor_id, self.cc_list, self.response_id, 'Requestor')

class Message(models.Model):
    _inherit = 'mail.message'

    declaration_email_message_id = fields.Many2one('declaration.record', string="History ID")


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    mail_template_type = fields.Selection(selection=[('response', 'Response Email'),
                                       ('border_crossing', 'Border Crossing Email'),
                                       ('owner', 'Owner Email')],
                                       string='Type')