from odoo import SUPERUSER_ID, api


def post_init_hook(env_or_cr, registry=None):
    env = env_or_cr if isinstance(env_or_cr, api.Environment) else api.Environment(env_or_cr, SUPERUSER_ID, {})

    shop_model = env["building.shop"].sudo()
    if shop_model.search_count([]):
        return

    records = []
    for floor in (1, 2):
        for row_code in ("A", "B"):
            for number in range(1, 21):
                records.append(
                    {
                        "name": f"F{floor}-{row_code}{number:02d}",
                        "floor": floor,
                        "row_code": row_code,
                        "shop_number": number,
                    }
                )
    shop_model.create(records)
