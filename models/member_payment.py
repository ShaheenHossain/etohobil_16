from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

class MemberPayment(models.Model):
    _name = 'member.payment'
    _description = 'Member Payment Record'

    member_id = fields.Many2one('res.partner', string="Member", required=True)
    base_amount = fields.Float(string="Base Amount") # compute='_compute_base_amount', store=True
    # selected_total = fields.Many2one('member.deposit.structure', string="Base Calculated Amount")
    current_amount = fields.Float(string="Current Amount", compute='_compute_current_amount', store=True)
    monthly_increment = fields.Float(string='Monthly Increment', default=1000)
    paid_amount = fields.Float(string="Paid Amount", default=0.0)
    due_amount = fields.Float(string="Due Amount", compute='_compute_due_amount', store=True)
    advance_amount = fields.Float(string="Advance Amount", compute='_compute_advance_amount', store=True)
    payment_date = fields.Date(string="Payment Date")
    status = fields.Selection([('paid', 'Paid'), ('due', 'Due')], string="Status", compute='_compute_status', store=True)

    member_payment_structure_ids = fields.One2many('member.deposit.structure', 'payment_id', string="Payment Structures")

    member_deposit_structure_id = fields.Many2one(
        'member.deposit.structure',
        string="Deposit Structure",
        ondelete='cascade'
    )


    def create_invoice(self):
        """Generate invoice for selected payment structures."""
        invoice_lines = []
        for payment_structure in self.member_payment_structure_ids.filtered('is_selected'):
            invoice_line_vals = {
                'product_id': payment_structure.payment_info.id,
                'quantity': 1,
                'price_unit': payment_structure.total_with_extra_amount,
                'name': payment_structure.payment_info.display_name,
            }
            invoice_lines.append((0, 0, invoice_line_vals))

        if invoice_lines:
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': self.member_id.id,
                'invoice_line_ids': invoice_lines,
            }
            self.env['account.move'].create(invoice_vals)



    #
    # member_payment_structure_ids = fields.One2many('member.deposit.structure', 'payment_id', string="Payment Structures")
    # grand_total_amount = fields.Float(string="Grand Total Amount", compute='_compute_grand_total', store=True)
    #
    # @api.depends('member_payment_structure_ids.total_with_extra_amount')
    # def _compute_grand_total(self):
    #     for record in self:
    #         record.grand_total_amount = sum(
    #             line.grand_total_amount for line in record.member_payment_structure_ids)
    #
    # @api.onchange('member_payment_structure_ids')
    # def _onchange_member_payment_structure_ids(self):
    #     self._compute_grand_total()

    #
    #
    # @api.depends('payment_structure_ids.total_with_extra_amount')
    # def _compute_base_amount(self):
    #     self.base_amount = sum(self.payment_structure_ids.mapped('total_with_extra_amount'))
    #
    #
    # @api.depends('payment_structure_ids.total_with_extra_amount')
    # def _compute_base_amount(self):
    #     for rec in self:
    #         # Calculate the sum of `total_with_extra_amount` for each `payment_structure_ids` record associated with `rec`
    #         rec.base_amount = sum(rec.payment_structure_ids.mapped('total_with_extra_amount'))
    #
    #
    # @api.depends('payment_structure_ids.total_with_extra_amount')
    # def _compute_base_amount(self):
    #     self.base_amount = sum(self.payment_structure_ids.mapped('total_with_extra_amount'))
    #
    # @api.depends('payment_structure_ids.total_with_extra_amount')
    # def _compute_base_amount(self):
    #     for record in self:
    #         # Calculate base amount by summing total_with_extra_amount from related payment structures
    #         total = sum(record.payment_structure_ids.mapped('total_with_extra_amount'))
    #         record.base_amount = total
    #
    # @api.depends('payment_structure_ids.total_with_extra_amount')
    # def _compute_base_amount(self):
    #     for record in self:
    #         # Calculate base amount by summing related payment structures' total_with_extra_amount
    #         total = sum(line.total_with_extra_amount for line in record.payment_structure_ids)
    #         record.base_amount = total
    #
    #
    # @api.depends('payment_structure_ids.total_with_extra_amount')
    # def _compute_base_amount(self):
    #     for record in self:
    #         # Calculate base amount by summing related payment structures' total_with_extra_amount
    #         total = sum(line.total_with_extra_amount for line in record.payment_structure_ids)
    #         record.base_amount = total
    #
    #         # Debug log for tracking calculation
    #         record.env['ir.logging'].sudo().create({
    #             'name': 'Member Payment',
    #             'type': 'server',
    #             'dbname': record._cr.dbname,
    #             'level': 'info',
    #             'message': f'Computed base amount for record {record.id}: {total}, from structures: {[line.total_with_extra_amount for line in record.payment_structure_ids]}',
    #             'path': 'member_payment.py',
    #             'func': '_compute_base_amount',
    #             'line': '28',
    #         })

    @api.depends('base_amount', 'create_date', 'monthly_increment')
    def _compute_current_amount(self):
        for record in self:
            if record.create_date:
                months = (datetime.now().year - record.create_date.year) * 12 + datetime.now().month - record.create_date.month
                record.current_amount = record.base_amount + (months * record.monthly_increment)
            else:
                record.current_amount = record.base_amount

    @api.depends('paid_amount', 'current_amount')
    def _compute_due_amount(self):
        for record in self:
            due = record.current_amount - record.paid_amount
            record.due_amount = due if due > 0 else 0

    @api.depends('paid_amount', 'current_amount')
    def _compute_advance_amount(self):
        for record in self:
            advance = record.paid_amount - record.current_amount
            record.advance_amount = advance if advance > 0 else 0

    @api.depends('due_amount')
    def _compute_status(self):
        for record in self:
            record.status = 'paid' if record.due_amount == 0 else 'due'

    def auto_generate_invoice(self):
        for record in self:
            if record.status == 'due':
                invoice_vals = {
                    'partner_id': record.member_id.id,
                    'move_type': 'out_invoice',
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': [(0, 0, {
                        'name': 'Monthly Due Payment',
                        'quantity': 1,
                        'price_unit': record.due_amount,
                    })],
                }
                self.env['account.move'].create(invoice_vals)


