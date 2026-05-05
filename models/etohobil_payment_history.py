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

    payment_date = fields.Date(string="Payment Date", required=True,
                               default=fields.Date.context_today)  # Changed from invoice_date
    amount = fields.Float(string="Amount", required=True)
    payment_type = fields.Selection([
        ('monthly', 'Monthly Deposit'),
        ('extra', 'Extra Payment'),
        ('advance', 'Advance Payment')
    ], string="Payment Type", required=True, default='monthly')
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check')
    ], string="Payment Method")
    reference = fields.Char(string="Reference Number")
    notes = fields.Text(string="Notes")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='draft')