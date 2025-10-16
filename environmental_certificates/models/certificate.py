import base64
import datetime
import io
from collections import namedtuple

from odoo import api, models, fields, _
from odoo.tools.mimetypes import guess_mimetype
from odoo.exceptions import ValidationError
from typing import Any

DAYS_TO_EXPIRY = 30

VALID = "valid"
EXPIRED = "expired"
EXPIRING = "expiring"
ALLOWED_MIME_TYPES = [
    "application/pdf",
    "image/jpeg",
    "image/png",
]
FILE_SIZE_LIMIT_MB = 20 * 1024 * 1024  # 20 MB


def group_certificates_by_status(
    certificates: list[tuple[str, str, Any]],
) -> dict:
    """Sort certificates in buckets by their status."""
    sorter_certificates = {VALID: [], EXPIRING: [], EXPIRED: []}

    for name, status, expiration_date in certificates:
        sorter_certificates[status].append((name, expiration_date))
    return sorter_certificates


class Certificate(models.Model):
    _name = "environment.certificate"
    _description = "Certificate"
    _inherit = ["mail.thread", "mail.activity.mixin"]

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
    document_name = fields.Char(
        string="Certificate Document Name", default="No Name"
    )
    status = fields.Selection(
        string="Certificate Status",
        selection=[
            (VALID, "Valid"),
            (EXPIRING, "Expiring"),
            (EXPIRED, "Expired"),
        ],
        store=True,
        tracking=True,
        compute="_compute_status",
    )
    producer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Producer",
    )
    color = fields.Html(string="Status", compute="_compute_status_display")
    download_url = fields.Html(
        string="Download URL", compute="_compute_download_url"
    )

    @api.depends("document")
    def _compute_download_url(self):
        for record in self:
            if record.document:
                url = (
                    f"/web/content?model={record._name}&id={record.id}"
                    "&field=document&download=true&"
                    f'filename={record.document_name or "certificate"}'
                )
                record.download_url = (
                    f'<a href="{url}" class="btn btn-sm btn-secondary" '
                    'title="Download Certificate"><i class="fa fa-download">'
                    "</i> Download</a>"
                )

    @api.constrains("issue_date", "expiration_date")
    def _check_dates(self):
        for record in self:
            if record.issue_date > fields.Date.today():
                raise ValidationError(
                    "Certificate Issue Date must be not later than today"
                )
            if record.expiration_date is False:
                continue
            if record.expiration_date <= record.issue_date:
                raise ValidationError(
                    "Certificate Expiration Date must be strictly after the Issue Date."
                )

    @api.constrains("document")
    def _check_document_type(self):
        for record in self:
            if not (document := base64.b64decode(record.document)):
                continue
            if guess_mimetype(document) not in ALLOWED_MIME_TYPES:
                raise ValidationError(
                    "Certificate Document must be a PDF, JPEG, or PNG file."
                )
            file = io.BytesIO(document)
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)

            if file_size > FILE_SIZE_LIMIT_MB:
                raise ValidationError(
                    "Certificate Document must be not bigger than 20MB."
                )

    @api.depends("issue_date", "expiration_date")
    def _compute_status(self):
        today = fields.Date.today()
        for record in self:
            if not record.expiration_date:
                record.status = VALID
                continue
            if record.expiration_date < today:
                record.status = EXPIRED
                continue
            days_until_expiry = (record.expiration_date - today).days
            if days_until_expiry < DAYS_TO_EXPIRY:
                record.status = EXPIRING
            else:
                record.status = VALID

    @api.depends("status")
    def _compute_status_display(self):
        colors = {
            VALID: "#28a745",  # Green
            EXPIRED: "#dc3545",  # Red
            EXPIRING: "#ffc107",  # Yellow
        }
        for record in self:
            color = colors.get(record.status, "#6c757d")
            circle_style = """
                height: 25px;
                width: 25px;
                background-color: {};
                border-radius: 50%;
                display: inline-block;""".format(
                color
            )
            record.color = f'<span style="{circle_style}"></span>'

    def check_validity(self):
        today = datetime.date.today()
        expiration_date = today + datetime.timedelta(days=DAYS_TO_EXPIRY)
        certificates_to_process = self.env["environment.certificate"].search(
            [
                ("expiration_date", "<", expiration_date),
            ]
        )

        for certificate in certificates_to_process:
            if certificate.expiration_date < today:
                certificate.status = EXPIRED
            else:
                certificate.status = EXPIRING

    @api.model
    def create(self, vals):
        certificate = super().create(vals)
        certificate._notify_admins(
            template="environmental_certificates"
            ".email_template_new_certificate_notification",
            subject="Certificate is created",
        )
        return certificate

    def write(self, vals):
        result = super().write(vals)
        if self.env.context.get("website_id"):
            self._notify_admins(
                template="environmental_certificates"
                ".email_template_updated_certificate_notification",
                subject="Certificate is modified",
            )

        return result

    def action_edit_certificate(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Edit Certificate",
            "res_model": "certificate.wizard",
            "view_mode": "form",
            "view_type": "form",
            "target": "new",
            "context": {
                "default_producer_id": self.producer_id.id,
                "default_type_id": self.type_id.id,
                "default_category_id": self.category_id.id,
                "default_issue_date": self.issue_date,
                "default_expiration_date": self.expiration_date,
                "default_document": self.document,
                "certificate_id": self.id,
            },
        }

    @api.model
    def send_status_notifications(self):
        supplier_group = self.env.ref(
            "environmental_certificates.group_supplier_portal",
            raise_if_not_found=False,
        )
        if not supplier_group:
            return

        for supplier in supplier_group.users:
            certificates_data = [
                (c.document_name, c.status, c.expiration_date)
                for c in supplier.partner_id.certificate_ids
            ]
            certificates_by_status = group_certificates_by_status(
                certificates_data
            )
            body, subject = self.create_notifications(
                supplier.id, certificates_by_status
            )
            if not body:
                continue
            self.send_emails_and_notifications(supplier, body, subject)

    def create_notifications(self, supplier_id: int, certificates: dict):
        body = None
        supplier_user = self.env["res.users"].browse(supplier_id)

        if certificates[EXPIRING] or certificates[EXPIRED]:
            document = namedtuple(
                "Document", ["document_name", "expiration_date"]
            )
            expiring_certificates = [
                document(
                    document_name=certificate[0],
                    expiration_date=certificate[1],
                )
                for certificate in certificates[EXPIRING]
            ]
            expired_certificates = [
                document(
                    document_name=certificate[0],
                    expiration_date=certificate[1],
                )
                for certificate in certificates[EXPIRED]
            ]
            mail_body = self.env["ir.qweb"]._render(
                "environmental_certificates.email_template_certificate_status",
                {
                    "partner": supplier_user.partner_id,
                    "expiring_certificates": expiring_certificates,
                    "expired_certificates": expired_certificates,
                },
            )
            body = self.env["mail.render.mixin"]._replace_local_links(mail_body)
            subject = "Your certificates status"
            return body, subject

        if not certificates.get(VALID):
            mail_body = self.env["ir.qweb"]._render(
                "environmental_certificates.email_template_certificate_status",
                {"partner": supplier_user.partner_id, "no_sertificates": True},
            )
            body = self.env["mail.render.mixin"]._replace_local_links(mail_body)
            subject = "Certificate Required"
            return body, subject

        return "", ""

    def send_emails_and_notifications(self, supplier, body, subject):
        """Send created emails and notifications"""
        supplier.partner_id.message_post(
            body=body,
            email_layout_xmlid="mail.mail_notification_light",
            subject=subject,
            subtype_xmlid="mail.mt_note",
        )
        self.env["mail.mail"].sudo().create(
            {
                "author_id": self.env.uid,
                "auto_delete": True,
                "body_html": body,
                "email_from": self.env.user.email_formatted,
                "email_to": supplier.email,
                "subject": subject,
            }
        ).send()

    def _get_admin_ids(self):
        admin_group = self.env.ref(
            "environmental_certificates.group_certificate_admin",
            raise_if_not_found=False,
        )
        if not admin_group:
            return []
        return admin_group.users.filtered(lambda u: u.email)

    def _notify_admins(self, template: str, subject: str):
        mail_body = self.env["ir.qweb"]._render(
            template,
            {
                "partner": self.producer_id,
                "document_name": self.document_name,
                "document_type": self.type_id.name,
            },
        )
        body = self.env["mail.render.mixin"]._replace_local_links(mail_body)
        admins = self._get_admin_ids()
        for admin in admins:
            self.env["mail.mail"].sudo().create(
                {
                    "author_id": self.env.uid,
                    "auto_delete": True,
                    "body_html": body,
                    "email_from": self.env.user.email_formatted,
                    "email_to": admin.email,
                    "subject": subject,
                }
            ).send()
        self.env.user.partner_id.message_post(
            body=body,
            subject=subject,
            message_type="notification",
        )
