from odoo import fields, models


class CertificateWizard(models.TransientModel):
    _name = "certificate.wizard"
    _description = "Certificate Creation Wizard"

    type_id = fields.Many2one(
        comodel_name="environment.certificate.type",
        string="Certificate Type",
        required=True,
    )
    category_id = fields.Many2one(
        comodel_name="environment.category",
        string="Certificate Category",
    )
    issue_date = fields.Date(
        string="Certificate Issue Date",
        required=True,
        tracking=True,
    )
    expiration_date = fields.Date(
        string="Certificate Expiration Date",
        tracking=True,
    )
    document = fields.Binary(string="Certificate Document", required=True)

    def action_save_or_update_certificate(self):
        certificate_id = self.env.context.get("certificate_id")
        vals = {
            "producer_id": self.env.context.get("default_producer_id"),
            "type_id": self.type_id.id,
            "category_id": self.category_id.id,
            "issue_date": self.issue_date,
            "expiration_date": self.expiration_date,
            "document": self.document,
        }

        if certificate_id:
            certificate = self.env["environment.certificate"].browse(
                certificate_id
            )
            certificate.write(vals)
        else:
            self.env["environment.certificate"].create(vals)
        return {"type": "ir.actions.act_window_close"}
