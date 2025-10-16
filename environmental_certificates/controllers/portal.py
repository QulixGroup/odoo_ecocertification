import base64
import datetime

from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import ValidationError
from odoo.http import request


def _populate_page_with_error_message(request, post: dict, message: str):
    """Helper to return error message to user"""
    request.session["error_message"] = message
    request.session["form_data"] = {
        k: v for k, v in post.items() if k != "certificate_file"
    }


class CustomerPortalCertificate(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "certificate_count" in counters:
            values["certificate_count"] = (
                request.env["res.groups"]
                .sudo()
                .search_count(
                    [
                        ("name", "ilike", "Supplier"),
                        (
                            "id",
                            "in",
                            [gr.id for gr in request.env.user.groups_id],
                        ),
                    ]
                )
            )

        return values

    @http.route(["/certificates"], type="http", auth="user", website=True)
    def portal_my_certificates(self):
        """Route to display a list of company's certificates.

        Supplier user has access to their own certificates only, not even
        to their company certificates.
        """
        Certificate = request.env["environment.certificate"]
        if not Certificate.search([("producer_id", "=", request.env.user.self.id)]):
            return request.redirect("/certificates/new")

        error_message = request.session.pop("error_message", None)
        success_message = request.session.pop("success_message", None)
        domain = [("producer_id", "=", request.env.user.self.id)]
        certificates = Certificate.search(domain, order="issue_date desc")
        values = {
            "certificates": certificates,
            "error_message": error_message,
            "success_message": success_message,
        }

        return request.render(
            "environmental_certificates.portal_listed_certificates", values
        )

    @http.route(
        ["/certificates/<int:certificate_id>/download"],
        type="http",
        auth="user",
        website=True,
    )
    def download_certificate(self, certificate_id):
        """Route to download company's certificates"""
        certificate = request.env["environment.certificate"].browse(certificate_id)
        filename = getattr(certificate, "document_name")

        return request.redirect(
            f"/web/content?model={certificate._name}&id={certificate.id}"
            f"&field=document&filename={filename}&download=true"
        )

    @http.route(
        ["/certificates/new"],
        type="http",
        auth="user",
        methods=["GET"],
        website=True,
    )
    def show_certificate_form(self):
        """Route to display the certificate upload form."""
        error_message = request.session.pop("error_message", None)
        form_data = request.session.pop("form_data", None)
        success_message = request.session.pop("success_message", None)
        certificate_types = request.env["environment.certificate.type"].search([])
        certificate_categories = request.env["environment.category"].search([])
        values = {
            "certificate_types": certificate_types,
            "certificate_categories": certificate_categories,
            "error_message": error_message,
            "form_data": form_data,
            "success_message": success_message,
        }
        return request.render(
            "environmental_certificates.portal_certificate_form",
            values,
        )

    @http.route(
        ["/certificates/new", "/certificates/<int:certificate_id>/renew"],
        type="http",
        auth="user",
        methods=["POST"],
        website=True,
    )
    def create_or_renew_certificate(self, certificate_id=None, **post):
        """Route to create company's certificates."""
        Certificate = request.env["environment.certificate"]
        file = post.get("certificate_file")
        expiration_date = post.get("expiration_date")
        category_id = post.get("certificate_category")

        if not (type_id := post.get("certificate_type")):
            _populate_page_with_error_message(
                request=request,
                post=post,
                message="Please select certificate type.",
            )
            return request.redirect("/certificates/new")

        certificate_vals = {
            "document_name": file.filename,
            "issue_date": (post.get("issue_date")),
            "expiration_date": (expiration_date or False),
            "producer_id": request.env.user.self.id,
            "document": base64.b64encode(file.read()),
            "type_id": int(type_id),
            "category_id": None if category_id == "" else int(category_id),
        }

        try:
            if certificate_id:
                certificate = Certificate.browse(int(certificate_id))
                certificate.sudo().write(certificate_vals)
                request.session["success_message"] = "Certificate renewed successfully"
                return request.redirect("/certificates")

            Certificate.sudo().create(certificate_vals)
            request.session["success_message"] = "Certificate uploaded successfully"
            # no errors - redirect to list view
            return request.redirect("/certificates")
        except ValidationError as e:
            _populate_page_with_error_message(
                request=request,
                post=post,
                message=str(e),
            )
            return request.redirect("/certificates/new")

    @http.route(
        ["/certificates/<int:certificate_id>"],
        type="http",
        auth="user",
        methods=["GET"],
        website=True,
    )
    def render_certificate_form(self, certificate_id):
        Certificate = request.env["environment.certificate"]
        certificate_object = Certificate.browse(certificate_id)
        certificate_types = request.env["environment.certificate.type"].search([])
        certificate_categories = request.env["environment.category"].search([])

        if certificate_object.expiration_date:
            date_of_expiry = certificate_object.expiration_date.strftime("%Y-%m-%d")
        else:
            date_of_expiry = ""

        form_data = {
            "certificate_type": str(certificate_object.type_id.id),
            "certificate_category": str(certificate_object.category_id.id),
            "issue_date": certificate_object.issue_date.strftime("%Y-%m-%d"),
            "expiration_date": date_of_expiry,
            "certificate_id": certificate_id,
        }
        values = {
            "certificate_types": certificate_types,
            "certificate_categories": certificate_categories,
            "form_data": form_data,
        }
        return request.render(
            "environmental_certificates.portal_certificate_form",
            values,
        )

    @http.route(
        ["/certificates/replace"],
        type="http",
        auth="user",
        website=True,
    )
    def replace_certificate(self, **post):
        """Handle file replace for existing certificate."""
        try:
            Certificate = request.env["environment.certificate"]
            certificate_id = int(post.get("certificate_id"))
            replace_file = post.get("replace_file")

            if not (replace_file and hasattr(replace_file, "read")):
                request.session["error_message"] = "No file selected for upload"
                return request.redirect(request.httprequest.referrer or "/certificates")

            certificate = Certificate.browse(certificate_id)

            if not certificate.exists():
                request.session["error_message"] = "Certificate not found"
                return request.redirect("/certificates")

            if not (certificate.producer_id.id == request.env.user.self.id):
                request.session["error_message"] = (
                    "You do not have the right to modify this certificate"
                )
                return request.redirect(request.httprequest.referrer or "/certificates")

            file_content = replace_file.read()

            try:
                certificate.sudo().write(
                    {
                        "document": base64.b64encode(file_content),
                        "document_name": replace_file.filename,
                    }
                )
            except ValidationError as e:
                request.session["error_message"] = str(e)
                return request.redirect(request.httprequest.referrer or "/certificates")

            request.session["success_message"] = (
                f"Certificate file successfully replaced with {replace_file.filename}"
            )
            return request.redirect("/certificates")

        except ValueError:
            request.session["error_message"] = "Invalid certificate ID"
        except Exception as e:
            request.session["error_message"] = f"An error occurred: {str(e)}"
