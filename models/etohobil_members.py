from email.policy import default

from googletrans import Translator

from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'eTohobil Members'

    sequence = fields.Integer(required=True, default=1)
    name_bn = fields.Char(string='Member Name Bangla')

    # name = fields.Char(string='Member Name')
    member_id = fields.Char(string='Member ID')
    _order = 'member_id asc'
    # active_member = fields.Boolean(string='Active Member')
    active_member = fields.Boolean(string="Active Member", default=False)
    mobile = fields.Char(string='Mobile Number')
    whatsapp = fields.Char(string='Whatsapp Number')
    email = fields.Char(string='Email')
    father_name = fields.Char(string="Father's Name")
    father_name_bn = fields.Char(string="Father's Name Bangla")
    mother_name = fields.Char(string="Mother's Name")
    mother_name_bn = fields.Char(string="Mother's Name Bangla")
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

    contact_address = fields.Text(compute="_compute_contact_address", string="Contact Address")

    is_committee_member = fields.Boolean(string="Committee Member")
    committee_designation = fields.Char(string="Designation")
    committee_start_date = fields.Date(string="Committee Start Date")
    committee_end_date = fields.Date(string="Committee End Date")


    _sql_constraints = [
        ('unique_member_id', 'UNIQUE(member_id)', 'Member ID must be unique!')
    ]

    @api.onchange('name')
    def _onchange_name_translation(self):
        if self.name:
            self.get_translated_value('name', 'name_bn')


    @api.onchange('father_name')
    def _onchange_father_name_translation(self):
        if self.father_name:
            self.get_translated_value('father_name', 'father_name_bn')


    @api.onchange('mother_name')
    def _onchange_mother_name_translation(self):
        if self.mother_name:
            self.get_translated_value('mother_name', 'mother_name_bn')


    def get_translated_value(self, input_field, translated_field):
        """
        Helper to translate English text to Bangla.
        Note: Ensure 'googletrans==4.0.0-rc1' is installed for better stability.
        """
        self.ensure_one()
        value_to_translate = getattr(self, input_field)

        if value_to_translate:
            try:
                translator = Translator()
                # 'bn' is the standard ISO code for Bengali
                result = translator.translate(value_to_translate, src='en', dest='bn')

                # Update the field only if it's currently empty
                if not getattr(self, translated_field):
                    setattr(self, translated_field, result.text)
            except Exception as e:
                # Log the error so the UI doesn't freeze if the API fails
                return {'warning': {'title': _('Translation Error'), 'message': str(e)}}

    def action_translate_existing_names(self):
        # Find records where name_bn is still empty
        partners = self.search([('name_bn', '=', False), ('name', '!=', False)])
        translator = Translator()

        for partner in partners:
            try:
                # Standardizing to 'bn' for Google Translate
                result = translator.translate(partner.name, src='en', dest='bn')
                partner.name_bn = result.text

                # Optional: Also translate father/mother names if they are empty
                if partner.father_name and not partner.father_name_bn:
                    f_result = translator.translate(partner.father_name, src='en', dest='bn')
                    partner.father_name_bn = f_result.text

                if partner.mother_name and not partner.mother_name_bn:
                    m_result = translator.translate(partner.mother_name, src='en', dest='bn')
                    partner.mother_name_bn = m_result.text

                # Commit after each record to avoid timeout if you have many members
                self.env.cr.commit()
            except Exception:
                continue

