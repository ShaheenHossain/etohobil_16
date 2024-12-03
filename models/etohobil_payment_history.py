from odoo import models, fields, api, _
from datetime import datetime

class MemberPaymentHistory(models.Model):
    _name = 'member.payment.history'
    _description = 'Payment History'

    member_id = fields.Many2one('res.partner', string="Member", required=True, ondelete='cascade')
    invoice_id = fields.Many2one('account.move', string="Invoice", required=True)
    invoice_date = fields.Date(related='invoice_id.invoice_date', string="Invoice Date", store=True)
    amount_paid = fields.Monetary(related='invoice_id.amount_total', string="Amount Paid", store=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.company.currency_id.id
    )



    # @api.model
    # def create_payment_history(self, invoice):
    #     self.env['member.payment.history'].create({
    #         'member_id': invoice.partner_id.id,
    #         'invoice_id': invoice.id,
    #         'amount_paid': invoice.amount_total,
    #     })
