from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ShopBooking(models.Model):
    _name = "shop.booking"
    _description = "Shop Booking"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(default="New", readonly=True, copy=False)
    shop_id = fields.Many2one("building.shop", required=True, tracking=True)
    visitor_name = fields.Char(required=True, tracking=True)
    visitor_email = fields.Char(required=True, tracking=True)
    visitor_phone = fields.Char(tracking=True)
    company_name = fields.Char(tracking=True)
    meeting_datetime = fields.Datetime(required=True, tracking=True)
    notes = fields.Text()
    partner_id = fields.Many2one("res.partner", readonly=True, copy=False, tracking=True)
    sale_order_id = fields.Many2one("sale.order", readonly=True, copy=False, tracking=True)
    status = fields.Selection(
        [
            ("requested", "Requested"),
            ("confirmed", "Confirmed"),
            ("cancelled", "Cancelled"),
        ],
        default="requested",
        required=True,
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = sequence.next_by_code("website_building_booking.booking") or "New"
        bookings = super().create(vals_list)
        bookings.mapped("shop_id")._refresh_status_from_bookings()
        return bookings

    def write(self, vals):
        previous_shops = self.mapped("shop_id")
        result = super().write(vals)
        (previous_shops | self.mapped("shop_id"))._refresh_status_from_bookings()
        return result

    def unlink(self):
        shops = self.mapped("shop_id")
        result = super().unlink()
        shops._refresh_status_from_bookings()
        return result

    @api.constrains("status", "shop_id")
    def _check_single_confirmed_booking(self):
        for booking in self:
            if booking.status != "confirmed":
                continue
            duplicate = self.search_count(
                [
                    ("id", "!=", booking.id),
                    ("shop_id", "=", booking.shop_id.id),
                    ("status", "=", "confirmed"),
                ]
            )
            if duplicate:
                raise ValidationError("Only one confirmed booking is allowed per shop.")

    def action_confirm(self):
        for booking in self:
            if booking.shop_id.active_booking_id and booking.shop_id.active_booking_id != booking:
                raise ValidationError("This shop already has another confirmed booking.")
        self.write({"status": "confirmed"})

    def action_cancel(self):
        self.write({"status": "cancelled"})

    def action_create_quotation(self):
        self.ensure_one()
        if self.sale_order_id:
            return self.action_view_quotation()

        partner = self.partner_id
        if not partner:
            partner_domain = []
            if self.visitor_email:
                partner_domain = [("email", "=", self.visitor_email)]
            partner = self.env["res.partner"].search(partner_domain, limit=1) if partner_domain else self.env["res.partner"]
            if not partner:
                partner_vals = {
                    "name": self.visitor_name,
                    "email": self.visitor_email,
                    "phone": self.visitor_phone,
                    "company_type": "person",
                }
                if self.company_name:
                    partner_vals["comment"] = f"Company: {self.company_name}"
                partner = self.env["res.partner"].create(partner_vals)
            self.partner_id = partner

        note_parts = [
            f"Booking Reference: {self.name}",
            f"Shop: {self.shop_id.display_label or self.shop_id.name}",
            f"Meeting Date: {fields.Datetime.to_string(self.meeting_datetime)}",
        ]
        if self.notes:
            note_parts.append(f"Visitor Notes: {self.notes}")

        order = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "origin": self.name,
                "client_order_ref": self.shop_id.name,
                "note": "\n".join(note_parts),
            }
        )
        self.sale_order_id = order
        self.message_post(body=f"Quotation {order.name} created.")
        return self.action_view_quotation()

    def action_view_quotation(self):
        self.ensure_one()
        if not self.sale_order_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "name": "Quotation",
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": self.sale_order_id.id,
            "target": "current",
        }
