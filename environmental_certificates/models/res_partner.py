from odoo import models, fields


class Partner(models.Model):
    _inherit = "res.partner"

    certificate_ids = fields.One2many(
        comodel_name="environment.certificate",
        inverse_name="producer_id",
        string="Certificates",
        tracking=True,
        help="List of certificates",
    )

    def action_add_certificate(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Create Certificate",
            "res_model": "certificate.wizard",
            "view_mode": "form",
            "view_type": "form",
            "target": "new",
            "context": {"default_producer_id": self.id},
        }
