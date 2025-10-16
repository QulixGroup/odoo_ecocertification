from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MyCategory(models.Model):
    _name = "environment.category"
    _inherit = "product.category"
    _description = "Environment Category"

    certificate_ids = fields.One2many(
        comodel_name="environment.certificate",
        inverse_name="category_id",
        string="Certificates",
        tracking=True,
        help="List of certificates",
    )
    parent_id = fields.Many2one(
        "environment.category",
        string="Parent Category",
        index=True,
        ondelete="cascade",
    )
    child_id = fields.One2many(
        "environment.category", "parent_id", string="Child Categories"
    )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_default_category(self):
        main_category = self.env.ref(
            'environmental_certificates.certificate_category_all',
            raise_if_not_found=False,
        )
        if main_category and main_category in self:
            raise UserError(
                _(
                    "You cannot delete this product category, it is the default generic category."
                )
            )
