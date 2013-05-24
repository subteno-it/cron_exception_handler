# -*- coding: utf-8 -*-
##############################################################################
#
#    cron_exception_handler module for OpenERP, Allow to send emails when an error occurs on cron
#    Copyright (C) 2013 SYLEAM Info Services (<http://www.Syleam.fr/>)
#              Sylvain Garancher <sylvain.garancher@syleam.fr>
#
#    This file is a part of cron_exception_handler
#
#    cron_exception_handler is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    cron_exception_handler is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import sys
import traceback
import openerp
from openerp.osv import osv
from openerp.osv import fields
from tools.translate import _


class ir_cron(osv.osv):
    _inherit = 'ir.cron'

    _columns = {
        'email_on_error': fields.boolean('Email on Error', help='If checked, a request will be created and an email will be sent to the user\'s adress if an error occurs during the execution of this task'),
    }

    _defaults = {
        'email_on_error': True,
    }

    def _handle_callback_exception(self, cr, uid, model_name, method_name, args, job_id, job_exception):
        """
        Create a res.request and send an email, if possible, when an error occurs during the execution of a scheduled task
        """
        super(ir_cron, self)._handle_callback_exception(cr, uid, model_name, method_name, args, job_id, job_exception)
        request = self.pool.get('res.request')

        cron = self.browse(cr, uid, job_id)
        valid_traceback = getattr(job_exception, 'traceback', sys.exc_info())
        formatted_traceback = "".join(traceback.format_exception(*valid_traceback))

        summary = _("""Exception during the scheduled job %s execution :
    Cron name : %s
    Model : %s
    Method : %s
    Arguments : %s

Technical details :
%s""") % (cron.id, cron.name, cron.model, cron.function, cron.args, formatted_traceback)

        # Add a note in the request if the user has no email address
        if cron.email_on_error:
            if not cron.user_id.user_email:
                summary = _('WARNING : An email was requested, but the user has no configured email !\n\n') + summary
                if not openerp.tools.config['email_from']:
                    summary = _('WARNING : An email was requested, but the system has no configured email !\n\n') + summary

        # Create the request
        request.create(cr, uid, {
            'name': _('Exception during cron'),
            'act_from': uid,
            'act_to': uid,
            'body': summary,
        })

        # Send the email, if needed
        if cron.email_on_error and cron.user_id.user_email:
            # Send the mail
            ir_mail_server = self.pool.get('ir.mail_server')
            email_from = openerp.tools.config['email_from'] or cron.user_id.user_email
            message = ir_mail_server.build_email(email_from, [cron.user_id.user_email], 'Error during OpenERP Cron', summary)
            ir_mail_server.send_email(cr, uid, message)

ir_cron()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
