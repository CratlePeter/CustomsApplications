# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date
import logging
import poplib
import base64
from imaplib import IMAP4, IMAP4_SSL
from poplib import POP3, POP3_SSL

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 50
MAIL_TIMEOUT = 60

# Workaround for Python 2.7.8 bug https://bugs.python.org/issue23906
poplib._MAXLINE = 65536


class FetchmailServer(models.Model):
    _inherit = 'fetchmail.server'
    
    user_ids = fields.Many2many('res.users', 'fetchmail_user_rel', 'fetchmail_user_id', 'user_fetchmail_id', string='Access Users')
    country_id = fields.Many2one('res.country', string='Country')

    # Called to process each message
    def process_incoming_mail(self, res_id):
        message_id = self.env['mail.message'].search([('res_id', '=', res_id)], limit=1)

        # We would like to know whether this email has an attachment that gives us a clue as to which
        # declarant_record we should attach it to
        dr_ducr = dr_epu = dr_entry = dr_doe = dr_reference = mrn = dr_type = ''
        if message_id and message_id.attachment_ids:
            for message_attach in message_id.attachment_ids:
                # Take a look at what's in the attachments to find references to look up declaration_record
                # .. but only if it's readable text
                if message_attach.mimetype == 'text/plain':
                    message_in_attachment = message_attach.index_content

                    # Parse the message given the different types
                    dr_type = "import"
                    if 'IMPORT PRE-LODGEMENT ADVICE' in message_in_attachment or \
                            'EXPORT ENTRY ACCEPTANCE ADVICE' in message_in_attachment or \
                            'IMPORT ENTRY ACCEPTANCE ADVICE' in message_in_attachment:

                        for message_line in message_in_attachment.splitlines():
                            if 'EXPORT ENTRY' in message_line:
                                dr_type = "export"
                            if 'Decln UCR' in message_line:
                                dr_ducr = message_line[
                                          message_line.find('Decln UCR') + 12: message_line.find('part')].strip()
                            if 'Entry:' in message_line:
                                dr_entry_data = message_line[message_line.find('Entry:') + 7: message_line.find(
                                    'SAD ')].strip()
                                dr_epu, dr_entry, doe = dr_entry_data.split('-')
                                doe_split = doe.split('/')
                                dr_doe = date(int(doe_split[2]), int(doe_split[1]), int(doe_split[0]))
                            if 'Declarant reference' in message_line:
                                dr_reference = message_line[
                                               message_line.find('Declarant reference') + 22:].strip()
                            if 'MRN' in message_line:
                                mrn = message_line[message_line.find('MRN') + 13:].strip()
                    _logger.debug('MRN: %s,DRef: %s, DUCR: %s, EPU: %s, Entry %s, DoE %s', mrn, dr_reference, dr_ducr,
                                  dr_epu, dr_entry, dr_doe)

            # Find the associated declaration_record
            existing_attachments = []
            dr_to_be_deleted = self.env['declaration.record'].search([('id', '=', res_id)], limit=1)
            declaration_record_id = self.env['declaration.record'].search(
                [('name', '=', dr_ducr), ('epu', '=', dr_epu), ('entry_no','=',dr_entry)], limit=1)
            if declaration_record_id:
                _logger.debug('we found a matching declaration_record for ducr %s, epu %s, entry no %s',dr_ducr, dr_epu, dr_entry)
                # If it already has attachments then we need to append to the list when we process the mail
                if declaration_record_id.attachment_ids:
                    _logger.debug('there are attachments already.')
                    for dec_attach in declaration_record_id.attachment_ids:
                        existing_attachments.append(dec_attach.id)
            else:
                _logger.debug('new declaration_record has been created')
                declaration_record_id = dr_to_be_deleted
                declaration_record_id.type = dr_type
                declaration_record_id.name = dr_ducr
                declaration_record_id.epu = dr_epu
                declaration_record_id.entry_no = dr_entry
                declaration_record_id.doe = dr_doe
                declaration_record_id.mrn = mrn
                declaration_record_id.internal_ref = dr_reference

            message_id.declaration_email_message_id = declaration_record_id.id
            if message_id.attachment_ids:
                _logger.debug('adding email attachments to d_r %s', declaration_record_id)
                for dec_attach in message_id.attachment_ids:
                    existing_attachments.append(dec_attach.id)
                    # Use supervisor mode to link the attachments to the new model
                    dec_attach.sudo().write({'res_id':declaration_record_id.id})

            # Update the d_r with all of the attachments
            declaration_record_id.attachment_ids = [(6, 0, existing_attachments)]

            # If we're using the new declaration_record then the ids will be the same
            if declaration_record_id != dr_to_be_deleted:
                # Delete the declaration_record that was created automatically
                _logger.debug ('attaching the mail message to declaration %s', declaration_record_id)
                message_id.sudo().write({'res_id':declaration_record_id.id})
                _logger.debug ('Removing declaration_record with id %s', dr_to_be_deleted)
                self.env['declaration.record'].search([('id', '=', dr_to_be_deleted.id)], limit=1).unlink()


    def fetch_mail(self):
        """ WARNING: meant for cron usage only - will commit() after each email! """
        additionnal_context = {
            'fetchmail_cron_running': True
        }
        MailThread = self.env['mail.thread']
        for server in self:
            _logger.info('start checking for new emails on %s server %s', server.server_type, server.name)
            additionnal_context['default_fetchmail_server_id'] = server.id
            additionnal_context['server_type'] = server.server_type
            count, failed = 0, 0
            imap_server = None
            pop_server = None
            if server.server_type == 'imap':
                try:
                    imap_server = server.connect()
                    imap_server.select()
                    result, data = imap_server.search(None, '(UNSEEN)')
                    for num in data[0].split():
                        res_id = None
                        result, data = imap_server.fetch(num, '(RFC822)')
                        imap_server.store(num, '-FLAGS', '\\Seen')
                        try:
                            res_id = MailThread.with_context(**additionnal_context).message_process(
                                server.object_id.model, data[0][1],
                                save_original=server.original,
                                strip_attachments=(not server.attach))

                            self.process_incoming_mail(res_id)
                        except Exception:
                            _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                            failed += 1
                        imap_server.store(num, '+FLAGS', '\\Seen')
                        self._cr.commit()
                        count += 1
                    _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", count, server.server_type, server.name, (count - failed), failed)
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if imap_server:
                        imap_server.close()
                        imap_server.logout()
            elif server.server_type == 'pop':
                try:
                    while True:
                        pop_server = server.connect()
                        (num_messages, total_size) = pop_server.stat()
                        pop_server.list()
                        for num in range(1, min(MAX_POP_MESSAGES, num_messages) + 1):
                            (header, messages, octets) = pop_server.retr(num)
                            message = (b'\n').join(messages)
                            res_id = None
                            try:
                                res_id = MailThread.with_context(**additionnal_context).message_process(
                                    server.object_id.model, message,
                                    save_original=server.original,
                                    strip_attachments=(not server.attach))
                                process_incoming_mail(res_id)

                                pop_server.dele(num)
                            except Exception:
                                _logger.info('Failed to process mail from %s server %s.', server.server_type, server.name, exc_info=True)
                                failed += 1
                            self.env.cr.commit()
                        if num_messages < MAX_POP_MESSAGES:
                            break
                        pop_server.quit()
                        _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", num_messages, server.server_type, server.name, (num_messages - failed), failed)
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.server_type, server.name, exc_info=True)
                finally:
                    if pop_server:
                        pop_server.quit()
            server.write({'date': fields.Datetime.now()})
        return True