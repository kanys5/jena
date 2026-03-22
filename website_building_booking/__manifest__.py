{
    "name": "Website Building Booking",
    "version": "18.0.1.0.0",
    "summary": "Website booking flow for a two-floor shop layout",
    "category": "Website",
    "author": "OpenAI",
    "license": "LGPL-3",
    "depends": ["website", "mail", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/shop_views.xml",
        "views/booking_views.xml",
        "views/website_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_building_booking/static/src/scss/website_building_booking.scss",
            "website_building_booking/static/src/js/website_building_booking.js",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": True,
}
