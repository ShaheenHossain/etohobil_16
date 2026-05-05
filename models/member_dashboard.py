from odoo import models, fields, api, _


class MemberDashboard(models.Model):
    _name = 'member.dashboard'
    _description = 'Member Dashboard'
    _rec_name = 'member_id'

    member_id = fields.Many2one('res.partner', string="Member", required=True)
    total_deposited = fields.Monetary(string="Total Deposited", currency_field='currency_id')
    total_due = fields.Monetary(string="Total Due", currency_field='currency_id')
    total_advance = fields.Monetary(string="Total Advance", currency_field='currency_id')
    monthly_deposit = fields.Float(string="Monthly Deposit Amount")
    last_payment_date = fields.Date(string="Last Payment Date")
    next_payment_due = fields.Date(string="Next Payment Due")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    payment_history_ids = fields.One2many('member.payment.history', 'member_id', string="Payment History")
    invoice_ids = fields.Many2many('account.move', string="Invoices")

    def compute_dashboard(self):
        for record in self:
            # Calculate from existing data
            structures = self.env['member.deposit.structure'].search([
                ('partner_id', '=', record.member_id.id)
            ])
            record.total_deposited = sum(structures.mapped('total_with_extra_amount'))

            payments = self.env['account.payment'].search([
                ('partner_id', '=', record.member_id.id),
                ('state', '=', 'posted')
            ])
            total_paid = sum(payments.mapped('amount'))
            record.total_due = record.total_deposited - total_paid if record.total_deposited > total_paid else 0
            record.total_advance = total_paid - record.total_deposited if total_paid > record.total_deposited else 0

