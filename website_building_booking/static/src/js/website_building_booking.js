/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.BuildingBookingModal = publicWidget.Widget.extend({
    selector: "#wrap",
    events: {
        "click .shop-tile.is-available": "_onShopClick",
        "click [data-close-modal='1']": "_onCloseModal",
    },

    start() {
        this.modal = document.getElementById("booking-modal");
        this.shopIdInput = document.getElementById("booking-shop-id");
        this.shopNameTarget = document.getElementById("booking-shop-name");

        if (this.shopIdInput?.value) {
            const preselected = document.querySelector(
                `.shop-tile[data-shop-id="${this.shopIdInput.value}"]`
            );
            if (preselected) {
                this._openForTile(preselected);
            }
        }
        return this._super(...arguments);
    },

    _onShopClick(ev) {
        this._openForTile(ev.currentTarget);
    },

    _openForTile(tile) {
        this.shopIdInput.value = tile.dataset.shopId;
        this.shopNameTarget.textContent = tile.dataset.shopName;
        this.modal.classList.add("is-open");
        this.modal.setAttribute("aria-hidden", "false");
    },

    _onCloseModal() {
        this.modal.classList.remove("is-open");
        this.modal.setAttribute("aria-hidden", "true");
    },
});
