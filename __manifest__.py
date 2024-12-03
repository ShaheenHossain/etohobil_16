{
    'name': 'Golden Life Samabaay Samity',
    'version': '16.0.0.0.1',
    'depends': ['base', 'mail', 'account', 'sale', 'web'],
    'data': [
        # 'views/mail_template_member_invoice.xml',
        'views/member_payment.xml',
        'views/etohobil_members.xml',
        'views/etohobil_payment_history.xml',
        # 'views/payment_record_views.xml',
        # 'views/payment_structure_form_view.xml',
        'views/member_deposit_structure.xml',
        # 'views/bank_deposit_views.xml',
        # 'views/property_asset_views.xml',
        # 'views/loan_management_views.xml',
        # 'data/payment_structure_data.xml',
        # 'reports/payment_slip_report.xml',
         'security/ir.model.access.csv',
         # 'data/payment.structure.csv',
         'data/member.deposit.structure.csv',
         'data/res.partner.csv',
    ],

    'assets': {
        'web.assets_backend': [
            # 'web/static/src/js/widgets/form_controller.js',  # Path to FormController
            # 'web/static/src/js/core/rpc.js',  # Path to rpc
            # 'etohobil/static/src/js/sync_amount.js',
        ]
    },

    'application': True,
}
