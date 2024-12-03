from email.policy import default

from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'eTohobil Members'

    sequence = fields.Integer(required=True, default=1)

    # name = fields.Char(string='Member Name')
    member_id = fields.Char(string='Member ID', required=True, unique=True)
    _order = 'member_id asc'
    active_member = fields.Boolean(string='Active Member')
    mobile = fields.Char(string='Mobile Number')
    whatsapp = fields.Char(string='Whatsapp Number')
    email = fields.Char(string='Email')
    father_name = fields.Char(string="Father's Name")
    mother_name = fields.Char(string="Mother's Name")
    date_of_brith = fields.Date(string='Date of Birth')
    nid = fields.Char(string='NID')
    present_address = fields.Text(string='Present Address')
    permanent_address = fields.Text(string='Permanent Address')
    occupation = fields.Text(string='Occupation')
    religion= fields.Selection([('hindu', 'Hindu'), ('muslim', 'Muslim'), ('khristan', 'Khristan'), ('budhist', 'Budhist')], string="Religion", default='muslim')
    marital_status = fields.Selection([('single', 'Single'), ('married', 'Married')], string='Marital Status', default="married")
    nominee_name = fields.Char(string='Nominee Name')
    relation_with_nominee = fields.Char(string='Relation with Nominee')
    photo = fields.Binary(string='Member Photo')
    nominee_photo = fields.Binary(string='Nominee Photo')
    deposited_amount = fields.Float(string='Total Deposited Amount', compute='_compute_deposited_amount')
    due_amount = fields.Float(string='Due Amount', compute='_compute_due_amount')


    is_committee_member = fields.Boolean(string="Committee Member")
    committee_designation = fields.Char(string="Designation")
    committee_start_date = fields.Date(string="Committee Start Date")
    committee_end_date = fields.Date(string="Committee End Date")

    # payment_record_ids = fields.One2many('payment.record', 'member_id', string='Payment Records')


    # @api.depends('payment_record_ids')
    # def _compute_deposited_amount(self):
    #     for member in self:
    #         total_deposit = sum(record.deposit_amount for record in member.payment_record_ids)
    #         member.deposited_amount = total_deposit
    #
    # @api.depends('payment_record_ids')
    # def _compute_due_amount(self):
    #     for member in self:
    #         total_due = sum(record.due_amount for record in member.payment_record_ids if record.due_amount > 0)
    #         member.due_amount = total_due

