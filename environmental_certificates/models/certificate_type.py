from odoo import models, fields


class CertificateType(models.Model):
    _name = "environment.certificate.type"
    _description = "Certificate Type"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Certificate Type",
        required=True,
        copy=False,
        translate=True,
        tracking=True,
    )

    _sql_constraints = [
        ("name_uniq", "UNIQUE(name)", "The certificate type name must be unique.")
    ]
