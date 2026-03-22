from collections import OrderedDict

from odoo import fields, http
from odoo.http import request


class WebsiteBuildingBookingController(http.Controller):
    def _layout_data(self):
        shops = request.env["building.shop"].sudo().search(
            [], order="floor asc, row_code asc, shop_number asc"
        )
        layout = OrderedDict()
        for floor in (1, 2):
            floor_rows = OrderedDict()
            for row_code in ("A", "B"):
                floor_rows[row_code] = shops.filtered(
                    lambda shop: shop.floor == floor and shop.row_code == row_code
                )
            layout[floor] = floor_rows
        return layout

    @http.route("/building-layout", type="http", auth="public", website=True)
    def building_layout(self, **kwargs):
        values = {
            "layout": self._layout_data(),
            "error": kwargs.get("error"),
            "selected_shop_id": int(kwargs.get("shop_id", 0)) if kwargs.get("shop_id") else False,
            "success": kwargs.get("success"),
        }
        return request.render("website_building_booking.building_layout_page", values)

    @http.route(
        "/building-layout/book",
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=True,
    )
    def submit_booking(self, **post):
        shop_id = int(post.get("shop_id", 0))
        shop = request.env["building.shop"].sudo().browse(shop_id).exists()
        if not shop or shop.status == "reserved":
            return request.redirect("/building-layout?error=shop_unavailable")

        meeting_datetime = post.get("meeting_datetime", "").replace("T", " ")
        if not fields.Datetime.to_datetime(meeting_datetime):
            return request.redirect(f"/building-layout?error=invalid_datetime&shop_id={shop.id}")

        vals = {
            "shop_id": shop.id,
            "visitor_name": post.get("visitor_name"),
            "visitor_email": post.get("visitor_email"),
            "visitor_phone": post.get("visitor_phone"),
            "company_name": post.get("company_name"),
            "meeting_datetime": fields.Datetime.to_datetime(meeting_datetime),
            "notes": post.get("notes"),
        }
        booking = request.env["shop.booking"].sudo().create(vals)
        booking.message_post(body="Booking request submitted from website.")
        return request.redirect(f"/building-layout?success=1&shop_id={shop.id}")
