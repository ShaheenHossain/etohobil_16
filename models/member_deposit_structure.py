from odoo import models, fields, api, _, SUPERUSER_ID
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from datetime import date

import logging

_logger = logging.getLogger(__name__)


class MemberDepositStructure(models.Model):
    _name = 'member.deposit.structure'
    _description = 'Member Payment Structure'


    payment_id = fields.Many2one('member.payment', string="Payment Record", ondelete='cascade')
    sequence = fields.Integer(required=True, default=1)
    sl_no = fields.Integer(string="Sl")
    subscription_fee = fields.Float(string="Fee")
    deposit_amount = fields.Float(string="Monthly")
    extra_amount = fields.Float(string="Ext Amt")
    start_date = fields.Date(string="Start Dt")
    end_date = fields.Date(string="End Dt")
    total_years = fields.Integer(string="Tot Yrs", compute='_compute_total_years_months', store=True)
    total_months = fields.Integer(string="T. Month", compute='_compute_total_years_months', store=True)
    subtotal_amount = fields.Float(string="Sub-Total", compute='_compute_totals', store=True)
    subtotal_subscription_amount = fields.Float(string="Sub- Fee", compute='_compute_totals', store=True)
    total_amount_with_subscription = fields.Float(string="Total+Fee", compute='_compute_totals', store=True)
    total_with_extra_amount = fields.Float(string="Total+Extra", compute='_compute_totals', store=True)
    is_selected = fields.Boolean(string="Is Selected", default=False)
    selected_total = fields.Float(string="Selected Total", compute="_compute_selected_total", store=True)
    payment_info = fields.Many2one('product.product', string="Payment Info", domain=[('type', '=', 'service')])
    sale_order_line_id = fields.Many2one('sale.order.line', string="Sale Order Line", ondelete='cascade')
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
    grand_total = fields.Monetary(string="Grand Total", compute="_compute_grand_total", store=False,
                                  currency_field='currency_id')
    base_current_amount = fields.Float(string="Base Curr Amt")
    partner_id = fields.Many2one('res.partner', string="Partner")

    member_transaction_ids = fields.One2many('member.deposit.structure', 'account_move_id', string="Member Deposit Transactions")
    account_move_id = fields.Many2one('account.move', string="Related Account Move")
    member_deposit_structure_id = fields.Many2one('account.move', string="Account Move", ondelete='cascade')
    taxes_id = fields.Many2many('account.tax', 'member_deposit_structure_tax_rel', 'deposit_structure_id', 'tax_id',
                                string="Taxes")
    supplier_taxes_id = fields.Many2many('account.tax', 'member_deposit_structure_account_tax_rel', 'member_id',
                                         'tax_id', string="Supplier Taxes")

    is_last_record = fields.Boolean(string="Is Last Record", compute='_compute_is_last_record', store=False)


    @api.depends('payment_id', 'sequence')
    def _compute_is_last_record(self):
        for record in self:
            records = self.search([('payment_id', '=', record.payment_id.id)])
            max_seq = max(records.mapped('sequence') or [0])
            record.is_last_record = (record.sequence == max_seq)



    def cron_update_last_end_date(self):
        """Update the last record's end date to current month's end date"""
        _logger.info("=== Starting monthly end date update ===")

        # Get current date and calculate end of current month
        today = fields.Date.today()
        # Calculate last day of current month
        next_month = today + relativedelta(months=1)
        end_of_current_month = next_month - relativedelta(days=next_month.day)

        _logger.info(f"Today: {today}, Target end date: {end_of_current_month}")

        updated_count = 0

        # Get all deposit structure records
        all_records = self.search([])

        if not all_records:
            _logger.warning("No deposit structure records found!")
            return

        # Group records by payment_id manually
        records_by_payment = {}
        for record in all_records:
            payment_key = record.payment_id.id if record.payment_id else None
            if payment_key not in records_by_payment:
                records_by_payment[payment_key] = []
            records_by_payment[payment_key].append(record)

        # For each payment group, find the record with highest sequence
        for payment_key, records in records_by_payment.items():
            # Sort records by sequence descending and get the first one
            sorted_records = sorted(records, key=lambda r: r.sequence or 0, reverse=True)
            if sorted_records:
                last_record = sorted_records[0]

                # Update if end_date is different
                if last_record.end_date != end_of_current_month:
                    last_record.write({
                        'end_date': end_of_current_month
                    })
                    # Force recomputation
                    last_record._compute_total_years_months()
                    last_record._compute_totals()

                    # Update associated product if exists
                    if last_record.payment_info:
                        last_record.payment_info.write({'end_date': end_of_current_month})
                        _logger.info(f"Updated product {last_record.payment_info.name}")

                    updated_count += 1
                    _logger.info(
                        f"Updated record ID {last_record.id} (Payment: {payment_key}, Sequence: {last_record.sequence})")
                else:
                    _logger.info(f"Record ID {last_record.id} already has correct end date")

        _logger.info(f"=== Monthly update completed. Updated {updated_count} records. ===")

    def update_end_dates_daily(self):
        """Run this daily to check and update end dates"""
        today = fields.Date.today()

        # Check if today is the last day of the month
        tomorrow = today + relativedelta(days=1)
        if tomorrow.month != today.month:  # Today is last day of month
            self.cron_update_last_end_date()
            return True
        return False

    @api.model
    def create(self, vals):
        # Auto-select new deposit structures
        if 'is_selected' not in vals:
            vals['is_selected'] = True
        return super(MemberDepositStructure, self).create(vals)

    def action_set_current_end_date(self):
        for record in self:
            if not record.is_last_record:
                raise UserError("Only the last record can be updated.")
            today = fields.Date.context_today(self)
            end_of_month = today.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)
            record.end_date = end_of_month
            record._compute_total_years_months()
            record._compute_totals()

    @api.depends('total_with_extra_amount')
    def _compute_grand_total(self):
        for record in self:
            total = sum(self.search([]).mapped('total_with_extra_amount'))
            record.grand_total = total

    @api.depends('deposit_amount', 'subscription_fee', 'extra_amount')
    def _compute_selected_total(self):
        for record in self:
            record.selected_total = record.deposit_amount + record.subscription_fee + record.extra_amount

    @api.depends('start_date', 'end_date')
    def _compute_total_years_months(self):
        for record in self:
            if record.start_date and record.end_date:
                delta = relativedelta(record.end_date, record.start_date)
                if delta.days > 0:
                    delta = relativedelta(years=delta.years, months=delta.months + 1)
                record.total_years = delta.years
                record.total_months = delta.years * 12 + delta.months
            else:
                record.total_years = 0
                record.total_months = 1

    @api.depends('deposit_amount', 'subscription_fee', 'total_months', 'extra_amount')
    def _compute_totals(self):
        for record in self:
            record.subtotal_amount = record.deposit_amount * record.total_months
            record.subtotal_subscription_amount = record.subscription_fee * record.total_months
            record.total_amount_with_subscription = record.subtotal_amount + record.subtotal_subscription_amount
            record.total_with_extra_amount = record.total_amount_with_subscription + record.extra_amount

    def convert_to_product(self):
        for record in self:
            if record.payment_info:
                raise UserError("This record has already been converted to a product.")

            record._compute_totals()
            record._compute_total_years_months()

            payment_name = record.payment_id.name if record.payment_id and hasattr(record.payment_id,
                                                                                   'name') else 'Payment'
            # Ensure the serial number (sl_no) is zero-padded to 2 digits
            sl_no_padded = str(record.sl_no).zfill(2)  # Convert to string and pad with zeros

            product_vals = {
                'name': f"{payment_name} - {sl_no_padded}",  # Use the zero-padded number
                'type': 'service',
                'list_price': record.total_with_extra_amount,  # Set from total_with_extra_amount
                'standard_price': record.total_amount_with_subscription,  # Set from total_amount_with_subscription
                'sl_no': record.sl_no,
                'subscription_fee': record.subscription_fee,
                'deposit_amount': record.deposit_amount,
                'extra_amount': record.extra_amount,
                'start_date': record.start_date,
                'end_date': record.end_date,
                'total_years': record.total_years,
                'total_months': record.total_months,
                'subtotal_amount': record.subtotal_amount,
                'subtotal_subscription_amount': record.subtotal_subscription_amount,
                'total_amount_with_subscription': record.total_amount_with_subscription,
                'total_with_extra_amount': record.total_with_extra_amount,
                'taxes_id': [(5, 0, 0)],  # Clear out any sales taxes
                'supplier_taxes_id': [(5, 0, 0)],  # Clear out any purchase taxes
            }
            product = self.env['product.product'].create(product_vals)
            record.payment_info = product.id


    def write(self, vals):
        res = super(MemberDepositStructure, self).write(vals)
        if not self.env.context.get('from_sync'):
            for record in self:
                if record.payment_info:
                    product_vals = {
                        'list_price': record.total_with_extra_amount,
                        'standard_price': record.total_amount_with_subscription,
                        'deposit_amount': record.deposit_amount,
                        'subscription_fee': record.subscription_fee,
                        'extra_amount': record.extra_amount,
                        'start_date': record.start_date,
                        'end_date': record.end_date,
                        'total_years': record.total_years,
                        'total_months': record.total_months,
                        'subtotal_amount': record.subtotal_amount,
                        'subtotal_subscription_amount': record.subtotal_subscription_amount,
                        'total_amount_with_subscription': record.total_amount_with_subscription,
                        'total_with_extra_amount': record.total_with_extra_amount,
                    }
                    record.payment_info.with_context(from_sync=True).write(product_vals)
        return res

    def update_last_record_end_date_auto(self):
        payments = self.env['member.payment'].search([])

        today = fields.Date.context_today(self)
        end_of_month = today.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)

        for payment in payments:
            last_record = self.search(
                [('payment_id', '=', payment.id)],
                order="sequence desc",
                limit=1
            )

            if last_record and last_record.end_date != end_of_month:
                last_record.write({'end_date': end_of_month})

    def read(self, fields=None, load='_classic_read'):
        self.update_last_record_end_date_auto()
        return super().read(fields, load)



    def uninstall_hook(cr, registry):
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Delete only products created from this module
        products = env['product.product'].search([
            ('is_deposit_product', '=', True)
        ])
        products.unlink()





class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sl_no = fields.Integer(string="Sl")
    subscription_fee = fields.Float(string="Fee")
    deposit_amount = fields.Float(string="Monthly")
    extra_amount = fields.Float(string="Extra")
    start_date = fields.Date(string="St. Date")
    end_date = fields.Date(string="End Date")
    total_years = fields.Integer(string="T. Years", compute='_compute_total_years_months', store=True)
    total_months = fields.Integer(string="T. Month", compute='_compute_total_years_months', store=True)
    subtotal_amount = fields.Float(string="Subtotal", compute='_compute_totals', store=True)
    subtotal_subscription_amount = fields.Float(string="Subtl Fee", compute='_compute_totals', store=True)
    total_amount_with_subscription = fields.Float(string="Total+Fee", compute='_compute_totals', store=True)
    total_with_extra_amount = fields.Float(string="Total+Extra", compute='_compute_totals', store=True)

    is_payment_product = fields.Boolean(string="Is Payment", default=True)

    is_selected = fields.Boolean(string="Is Selected", default=False,
                                 help="Check this to select this product for invoices")

    # Add this field to your existing ProductTemplate class
    add_to_invoice = fields.Boolean(string="Add to Invoice", default=False,
                                    help="Check this to automatically add this product to invoices")


    @api.constrains('is_payment_product', 'deposit_amount', 'subscription_fee', 'extra_amount')
    def _check_payment_product_fields(self):
        for record in self:
            if record.is_payment_product and not (record.deposit_amount and record.subscription_fee):
                raise UserError("Payment products must have Deposit Amount and Subscription Fee filled!")

    @api.depends('deposit_amount', 'subscription_fee', 'extra_amount')
    def _compute_selected_total(self):
        for record in self:
            record.selected_total = record.deposit_amount + record.subscription_fee + record.extra_amount

    def action_calculate_selected_total(self):
        for record in self:
            record._compute_selected_total()

    @api.depends('start_date', 'end_date')
    def _compute_total_years_months(self):
        for record in self:
            if record.start_date and record.end_date:
                delta = relativedelta(record.end_date, record.start_date)
                if delta.days > 0:
                    delta = relativedelta(years=delta.years, months=delta.months + 1)
                record.total_years = delta.years
                record.total_months = delta.years * 12 + delta.months
            else:
                record.total_years = 0
                record.total_months = 1


    @api.depends('deposit_amount', 'subscription_fee', 'total_months', 'extra_amount', 'is_payment_product')
    def _compute_totals(self):
        for record in self:
            if record.is_payment_product:
                record.subtotal_amount = record.deposit_amount * record.total_months
                record.subtotal_subscription_amount = record.subscription_fee * record.total_months
                record.total_amount_with_subscription = record.subtotal_amount + record.subtotal_subscription_amount
                record.total_with_extra_amount = record.total_amount_with_subscription + record.extra_amount
            else:
                # Reset custom fields when not a payment product
                record.subtotal_amount = 0.0
                record.subtotal_subscription_amount = 0.0
                record.total_amount_with_subscription = 0.0
                record.total_with_extra_amount = 0.0


    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if not self.env.context.get('from_sync'):
            for product in self:
                structure = self.env['member.deposit.structure'].search([('payment_info', '=', product.id)], limit=1)
                if structure:
                    structure_vals = {
                        'deposit_amount': product.deposit_amount,
                        'subscription_fee': product.subscription_fee,
                        'extra_amount': product.extra_amount,
                        'start_date': product.start_date,
                        'end_date': product.end_date,
                    }
                    structure.with_context(from_sync=True).write(structure_vals)
        return res

    # Ensure that `create_bill` logic correctly refers to the product price
    @api.model
    def create_bill(self, order):
        # If the product is a payment product, ensure the price is correctly computed
        for line in order.order_line:
            if line.product_id.is_payment_product:
                line.price_unit = line.product_id.total_with_extra_amount
            else:
                line.price_unit = line.product_id.lst_price  # Or your normal price logic here
        return super(ProductTemplate, self).create_bill(order)


    def uninstall_hook(cr, registry):
        """Remove all products created by this module during uninstall"""
        env = api.Environment(cr, SUPERUSER_ID, {})

        # Delete only products created from this module
        # Using a specific field to identify them
        products = env['product.product'].search([
            ('is_payment_product', '=', True)  # Your custom field
        ])

        if products:
            _logger.info(f"Uninstalling module: Deleting {len(products)} payment products")
            products.unlink()

        # Also delete product templates
        product_templates = env['product.template'].search([
            ('is_payment_product', '=', True)
        ])

        if product_templates:
            _logger.info(f"Uninstalling module: Deleting {len(product_templates)} payment product templates")
            product_templates.unlink()

        _logger.info("Module uninstall completed - All payment products removed")




class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    deposit_amount = fields.Float(string="Monthly")
    subscription_fee = fields.Float(string="Fee")
    extra_amount = fields.Float(string="Extra")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    total_years = fields.Integer(string="Total Years", compute='_compute_total_years_months', store=True)
    total_months = fields.Integer(string="Total Months", compute='_compute_total_years_months', store=True)
    subtotal_amount = fields.Float(string="Subtotal Amount", compute='_compute_totals', store=True)
    subtotal_subscription_amount = fields.Float(string="Subtotal Fee", compute='_compute_totals', store=True)
    total_amount_with_subscription = fields.Float(string="Total with Fee", compute='_compute_totals', store=True)
    total_with_extra_amount = fields.Float(string="Total with Extra", compute='_compute_totals', store=True)
    authorized_transaction_ids = fields.One2many('member.deposit.structure', 'sale_order_line_id',  string="Authorized Transactions")

    partner_credit_warning = fields.Boolean("Partner Credit Warning")

    @api.onchange('product_id')
    def _onchange_product_id_custom(self):
        """Update custom fields based on selected product."""
        if self.product_id:
            # Fetch product values
            self.deposit_amount = self.product_id.deposit_amount
            self.subscription_fee = self.product_id.subscription_fee
            self.extra_amount = self.product_id.extra_amount
            self.start_date = self.product_id.start_date
            self.end_date = self.product_id.end_date
            self.total_years = self.product_id.total_years
            self.total_months = self.product_id.total_months
            self.subtotal_amount = self.product_id.subtotal_amount
            self.subtotal_subscription_amount = self.product_id.subtotal_subscription_amount
            self.total_amount_with_subscription = self.product_id.total_amount_with_subscription
            self.total_with_extra_amount = self.product_id.total_with_extra_amount
            self.product_uom_qty = self.product_id.total_months

    @api.depends('start_date', 'end_date')
    def _compute_total_years_months(self):
        for record in self:
            if record.start_date and record.end_date:
                # Calculate the difference between dates
                delta = relativedelta(record.end_date, record.start_date)
                # Add 1 to include the end month
                total_months = delta.years * 12 + delta.months + 1
                record.total_years = delta.years
                record.total_months = max(total_months, 1)  # Ensure minimum 1 month
            else:
                record.total_years = 0
                record.total_months = 1



    @api.depends('deposit_amount', 'subscription_fee', 'total_months', 'extra_amount')
    def _compute_totals(self):
        for line in self:
            line.subtotal_amount = line.deposit_amount * line.total_months
            line.subtotal_subscription_amount = line.subscription_fee * line.total_months
            line.total_amount_with_subscription = line.subtotal_amount + line.subtotal_subscription_amount
            line.total_with_extra_amount = line.total_amount_with_subscription + line.extra_amount
            line.price_subtotal = line.total_with_extra_amount
            # _logger.debug(f"Computed subtotal: {line.price_subtotal}, Total with Extra: {line.total_with_extra_amount}")
            line.product_uom_qty = line.total_months

    @api.depends('total_with_extra_amount', 'product_uom_qty')
    def _compute_amount(self):
        for line in self:
            line.price_subtotal = line.total_with_extra_amount
            line.product_uom_qty = 1
            line.price_unit = line.total_with_extra_amount

    @api.model
    def create(self, vals):
        if 'start_date' in vals and 'end_date' in vals:
            start_date = fields.Date.from_string(vals.get('start_date'))
            end_date = fields.Date.from_string(vals.get('end_date'))
            if start_date and end_date:
                delta = relativedelta(end_date, start_date)
                vals['total_months'] = delta.years * 12 + delta.months + 1
        return super(SaleOrderLine, self).create(vals)

    def write(self, vals):
        if 'start_date' in vals or 'end_date' in vals:
            for record in self:
                start_date = vals.get('start_date', record.start_date)
                end_date = vals.get('end_date', record.end_date)
                if start_date and end_date:
                    delta = relativedelta(end_date, start_date)
                    vals['total_months'] = delta.years * 12 + delta.months + 1
        return super(SaleOrderLine, self).write(vals)

    def _prepare_invoice_line(self, **optional_values):
        invoice_line_vals = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)

        invoice_line_vals.update({
            'deposit_amount': self.deposit_amount,
            'subscription_fee': self.subscription_fee,
            'extra_amount': self.extra_amount,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'total_years': self.total_years,
            'total_months': self.total_months,
            'subtotal_amount': self.subtotal_amount,
            'subtotal_subscription_amount': self.subtotal_subscription_amount,
            'total_amount_with_subscription': self.total_amount_with_subscription,
            'total_with_extra_amount': self.total_with_extra_amount,
            # 'amount_total': self.amount_total,
        })
        return invoice_line_vals


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount')

    def _prepare_invoice_line(self, line):
        res = super(SaleOrder, self)._prepare_invoice_line(line)
        res.update({
            'deposit_amount': line.deposit_amount,
            'subscription_fee': line.subscription_fee,
            'extra_amount': line.extra_amount,
            'start_date': line.start_date,
            'end_date': line.end_date,
            'total_years': line.total_years,
            'total_months': line.total_months,
            'subtotal_amount': line.subtotal_amount,
            'subtotal_subscription_amount': line.subtotal_subscription_amount,
            'total_amount_with_subscription': line.total_amount_with_subscription,
            'total_with_extra_amount': line.total_with_extra_amount,
            'price_unit': line.total_with_extra_amount,
            'quantity': 1,
        })
        return res

    @api.depends('order_line.price_total', 'currency_id')
    def _compute_amount(self):
        for order in self:
            order.amount_total = sum(order.order_line.mapped('price_total'))


    customer_invoice_total = fields.Monetary(
        string="Total Invoice Amount",
        compute='_compute_customer_invoice_total',
        currency_field='currency_id'
    )

    @api.depends('partner_id')
    def _compute_customer_invoice_total(self):
        for order in self:
            if order.partner_id:
                invoices = self.env['account.move'].search([
                    ('partner_id', '=', order.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    # ('state', '=', 'posted')  # Only consider posted invoices
                ])
                order.customer_invoice_total = sum(invoices.mapped('amount_total'))
            else:
                order.customer_invoice_total = 0.0


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    deposit_amount = fields.Float(string="Monthly")
    subscription_fee = fields.Float(string="Fee")
    extra_amount = fields.Float(string="Extra")
    start_date = fields.Date(string="St. Date")
    end_date = fields.Date(string="End Date")
    total_years = fields.Integer(string="T. Years", compute='_compute_total_years_months', store=True)
    total_months = fields.Integer(string="T. Months", compute='_compute_total_years_months', store=True)
    subtotal_amount = fields.Float(string="Subtotal", compute='_compute_totals', store=True, readonly=True)
    subtotal_subscription_amount = fields.Float(string="Subtl Fee", compute='_compute_totals', store=True, readonly=True)
    total_amount_with_subscription = fields.Float(string="Total+Fee", compute='_compute_totals', store=True, readonly=True)
    total_with_extra_amount = fields.Float(string="Total+Extra", compute='_compute_totals', store=True, readonly=True)
    member_deposit_structure_id = fields.Many2one('member.deposit.structure', string="Member Deposit Structure", ondelete='cascade')

    @api.onchange('product_id')
    def _onchange_product_id_custom(self):
        if self.product_id:
            if self.product_id.is_payment_product:
                self.deposit_amount = self.product_id.deposit_amount
                self.subscription_fee = self.product_id.subscription_fee
                self.extra_amount = self.product_id.extra_amount
                self.start_date = self.product_id.start_date
                self.end_date = self.product_id.end_date
            else:
                # Reset custom fields for non-payment products
                self.deposit_amount = 0.0
                self.subscription_fee = 0.0
                self.extra_amount = 0.0
                self.start_date = False
                self.end_date = False

    @api.depends('start_date', 'end_date')
    def _compute_total_years_months(self):
        """ Calculate total years and months between start_date and end_date. """
        for record in self:
            if record.start_date and record.end_date:
                delta = relativedelta(record.end_date, record.start_date)
                total_months = delta.years * 12 + delta.months + 1
                record.total_years = delta.years
                record.total_months = max(total_months, 1)
            else:
                record.total_years = 0
                record.total_months = 1

    @api.model
    def create(self, vals):
        """ Set default quantity for new lines. """
        if 'quantity' not in vals:
            vals['quantity'] = 1
        return super(AccountMoveLine, self).create(vals)

    @api.depends('quantity', 'price_unit')
    def _compute_price_unit(self):
        """ Ensure price_unit is recalculated when needed. """
        for line in self:
            if line.price_subtotal and line.quantity:
                line.price_unit = line.price_subtotal / line.quantity


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Basic Fields
    sl_no = fields.Integer(string="Sl")
    subscription_fee = fields.Float(string="Fee")
    deposit_amount = fields.Float(string="Monthly")
    extra_amount = fields.Float(string="Extra")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    # Computed Fields
    total_years = fields.Integer(string="Total Years", compute='_compute_total_years_months', store=True)
    total_months = fields.Integer(string="Total Months", compute='_compute_total_years_months', store=True)
    subtotal_amount = fields.Float(string="Subtotal Amount", compute='_compute_totals', store=True)
    subtotal_subscription_amount = fields.Float(string="Subtotal Fee", compute='_compute_totals', store=True)
    total_amount_with_subscription = fields.Float(string="Total+Fee", compute='_compute_totals', store=True)
    total_with_extra_amount = fields.Float(string="Total+Extra", compute='_compute_totals', store=True)

    # current_base_amount = fields.Float(string="Current Base Amount", compute="_compute_current_base_amount", store=True)
    current_base_amount = fields.Float(string="Current Base Amount", compute="_compute_current_base_amount", store=False, readonly=True)

    total_base_current_amount = fields.Float(string="Base Curr. Amount", compute="_compute_total_base_current_amount", store=True)
    amount_due = fields.Float(string="Amount Due", compute="_compute_amount_due", store=False, readonly=True)

    # Payment Fields
    total_deposited_amount = fields.Monetary(string="Deposited Amount", compute="_compute_total_deposited_amount", store=True, currency_field='currency_id')
    remaining_amount = fields.Monetary(string="Remaining Amount", compute="_compute_remaining_and_advance", store=True, currency_field='currency_id')
    advance_payment = fields.Monetary(string="Advance Payment", compute="_compute_remaining_and_advance", store=True, currency_field='currency_id')
    show_advance_payment = fields.Boolean(string="Show Advance Payment", compute="_compute_remaining_and_advance", store=True)

    # Related Field
    member_id = fields.Char(related='partner_id.member_id', string="Member ID", readonly=True, store=True)

    # Override Move Type Label
    move_type = fields.Selection(selection_add=[
        ('out_invoice', 'Payment Invoice')
    ])

    # Computation Methods
    @api.depends('start_date', 'end_date')
    def _compute_total_years_months(self):
        for record in self:
            if record.start_date and record.end_date:
                delta = relativedelta(record.end_date, record.start_date)
                if delta.days > 0:
                    delta = relativedelta(years=delta.years, months=delta.months + 1)
                record.total_years = delta.years
                record.total_months = delta.years * 12 + delta.months
            else:
                record.total_years = 0
                record.total_months = 1

    @api.depends('deposit_amount', 'subscription_fee', 'total_months', 'extra_amount')
    def _compute_totals(self):
        for record in self:
            record.subtotal_amount = record.deposit_amount * record.total_months
            record.subtotal_subscription_amount = record.subscription_fee * record.total_months
            record.total_amount_with_subscription = record.subtotal_amount + record.subtotal_subscription_amount
            record.total_with_extra_amount = record.total_amount_with_subscription + record.extra_amount

    @api.depends('partner_id')
    def _compute_total_base_current_amount(self):
        for record in self:
            member_payment_records = self.env['member.deposit.structure'].search([
                ('partner_id', '=', record.partner_id.id)
            ])
            record.total_base_current_amount = sum(member_payment_records.mapped('base_current_amount'))

    @api.depends()
    def _compute_current_base_amount(self):
        for record in self:
            grand_total = self.env['member.deposit.structure'].search([]).mapped('total_with_extra_amount')
            record.current_base_amount = sum(grand_total)


    @api.depends('line_ids.payment_id', 'line_ids.payment_id.state')
    def _compute_total_deposited_amount(self):
        for record in self:
            payments = self.env['account.payment'].search([
                ('partner_id', '=', record.partner_id.id),
                ('state', '=', 'posted')
            ])
            record.total_deposited_amount = sum(payments.mapped('amount'))

    @api.depends('total_deposited_amount', 'current_base_amount')
    def _compute_remaining_and_advance(self):
        for record in self:
            if record.total_deposited_amount >= record.current_base_amount:
                record.remaining_amount = 0.0
                record.advance_payment = record.total_deposited_amount - record.current_base_amount
                record.show_advance_payment = record.advance_payment > 0
            else:
                record.remaining_amount = record.current_base_amount - record.total_deposited_amount
                record.advance_payment = 0.0
                record.show_advance_payment = False

    @api.depends('total_deposited_amount', 'current_base_amount')
    def _compute_amount_due(self):
        for record in self:
            if record.total_deposited_amount > record.current_base_amount:
                record.amount_due = record.total_deposited_amount - record.current_base_amount
            else:
                record.amount_due = max(0.0, record.current_base_amount - record.total_deposited_amount)

    # Actions
    def action_recalculate_deposit(self):
        for record in self:
            record._compute_total_deposited_amount()


    # Constraints
    @api.constrains('partner_id', 'move_type')
    def _check_member_field(self):
        for record in self:
            if record.move_type == 'out_invoice' and not record.partner_id:
                raise UserError("The field 'Member' is required, please complete it to validate the Member Invoice.")

    def action_add_all_products(self):
        """Add all payment products to the invoice"""

        # First try to add from deposit structures
        deposit_structures = self.env['member.deposit.structure'].search([
            ('partner_id', '=', self.partner_id.id),
            ('payment_info', '!=', False)
        ])

        added_count = 0

        if deposit_structures:
            for structure in deposit_structures:
                existing_line = self.invoice_line_ids.filtered(
                    lambda line: line.product_id.id == structure.payment_info.id
                )

                if not existing_line:
                    line_vals = {
                        'move_id': self.id,
                        'product_id': structure.payment_info.id,
                        'quantity': 1,
                        'deposit_amount': structure.deposit_amount,
                        'subscription_fee': structure.subscription_fee,
                        'extra_amount': structure.extra_amount,
                        'start_date': structure.start_date,
                        'end_date': structure.end_date,
                        'price_unit': structure.total_with_extra_amount,
                    }
                    self.env['account.move.line'].create(line_vals)
                    added_count += 1
        else:
            product_templates = self.env['product.template'].search([
                ('is_payment_product', '=', True)
            ])

            for product in product_templates:
                existing_line = self.invoice_line_ids.filtered(
                    lambda line: line.product_id.id == product.product_variant_id.id
                )

                if not existing_line:
                    line_vals = {
                        'move_id': self.id,
                        'product_id': product.product_variant_id.id,
                        'quantity': 1,
                        'deposit_amount': product.deposit_amount,
                        'subscription_fee': product.subscription_fee,
                        'extra_amount': product.extra_amount,
                        'start_date': product.start_date,
                        'end_date': product.end_date,
                        'price_unit': product.list_price or product.standard_price or 0.0,
                    }
                    self.env['account.move.line'].create(line_vals)
                    added_count += 1

        if added_count > 0:
            # Refresh the form view to show new lines
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': self.id,
                'view_mode': 'form',
                'view_id': self.env.ref('account.view_move_form').id,
                'target': 'current',
                'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},
            }
        else:
            raise UserError("No products were added. They may already exist in the invoice.")






class ResPartner(models.Model):
    _inherit = 'res.partner'

    deposit_structure_ids = fields.One2many('member.deposit.structure', 'partner_id', string="Deposit Structures")
    total_with_extra_amount = fields.Float(string="Total with Extra Amount", default=0.0)
    related_account_move_id = fields.Many2one('account.move', string="Related Account Move")

    payment_history_ids = fields.One2many('member.payment.history', 'member_id', string="Payment History")



class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _update_related_invoices(self):
        for payment in self:
            invoices = self.env['account.move'].search([
                ('partner_id', '=', payment.partner_id.id),
                ('move_type', '=', 'out_invoice')
            ])
            invoices._compute_total_deposited_amount()
            invoices._compute_remaining_and_advance()

    def action_post(self):
        res = super().action_post()
        self._update_related_invoices()
        return res

    def write(self, vals):
        res = super().write(vals)
        self._update_related_invoices()
        return res

