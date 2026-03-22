from odoo import api, fields, models


class BuildingShop(models.Model):
    _name = "building.shop"
    _description = "Building Shop"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "floor, row_code, shop_number"

    name = fields.Char(required=True, tracking=True)
    floor = fields.Integer(required=True, tracking=True)
    row_code = fields.Selection(
        [("A", "Row A"), ("B", "Row B")], required=True, tracking=True
    )
    row_name = fields.Char(compute="_compute_row_name", store=True)
    shop_number = fields.Integer(required=True, tracking=True)
    status = fields.Selection(
        [("available", "Available"), ("reserved", "Reserved")],
        default="available",
        required=True,
        tracking=True,
    )
    booking_ids = fields.One2many("shop.booking", "shop_id", string="Bookings")
    active_booking_id = fields.Many2one(
        "shop.booking",
        compute="_compute_active_booking_id",
        store=True,
        string="Confirmed Booking",
    )
    display_label = fields.Char(compute="_compute_display_label")

    _sql_constraints = [
        (
            "shop_unique_layout",
            "unique(floor, row_code, shop_number)",
            "A shop already exists at this floor, row, and position.",
        )
    ]

    @api.depends("booking_ids.status")
    def _compute_active_booking_id(self):
        for shop in self:
            confirmed = shop.booking_ids.filtered(lambda booking: booking.status == "confirmed")
            shop.active_booking_id = confirmed[:1].id if confirmed else False

    @api.depends("row_code")
    def _compute_row_name(self):
        selection = dict(self._fields["row_code"].selection)
        for shop in self:
            shop.row_name = selection.get(shop.row_code, "")

    @api.depends("floor", "row_code", "shop_number")
    def _compute_display_label(self):
        for shop in self:
            shop.display_label = f"Floor {shop.floor} / Row {shop.row_code} / Shop {shop.shop_number:02d}"

    def _refresh_status_from_bookings(self):
        for shop in self:
            has_confirmed = bool(shop.booking_ids.filtered(lambda booking: booking.status == "confirmed"))
            shop.status = "reserved" if has_confirmed else "available"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") and vals.get("floor") and vals.get("row_code") and vals.get("shop_number"):
                vals["name"] = f"F{vals['floor']}-{vals['row_code']}{int(vals['shop_number']):02d}"
        return super().create(vals_list)
