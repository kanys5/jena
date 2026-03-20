# -*- coding: utf-8 -*-
import datetime
from odoo import fields, models, api
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from collections import Counter
import json, ast

class PosConfig(models.Model):
    _inherit = 'pos.config'

    omax_session_z_report = fields.Boolean(string='Session Z Report', help='This will allow to print Session Z Report directly from POS screen')
    show_details_in_session_z_report = fields.Boolean(string='Show Details in Session Z Report')
    show_product_wise_detail = fields.Boolean(string='Product Or Variant Wise Detail')
    product_or_variant = fields.Selection([
        ('product', 'Product'),
        ('variant', 'Product Variant'),], default='variant', string='Product Or Variant')
    show_category_wise_sales = fields.Boolean(string='Category Wise Sales')
    show_taxes_detail = fields.Boolean(string='Taxes Detail')
    show_pricelist_detail = fields.Boolean(string='Pricelist Detail')
    show_payment_detail = fields.Boolean(string='Payment Detail')
    show_cash_in_out_details = fields.Boolean(string='Cash In Out Details')

class ResConfigZreport(models.TransientModel):
    _inherit = 'res.config.settings'

    omax_session_z_report = fields.Boolean(related='pos_config_id.omax_session_z_report', readonly=False)
    show_details_in_session_z_report = fields.Boolean(related='pos_config_id.show_details_in_session_z_report', readonly=False)
    show_product_wise_detail = fields.Boolean(related='pos_config_id.show_product_wise_detail', readonly=False)
    product_or_variant = fields.Selection(related='pos_config_id.product_or_variant', readonly=False)
    show_category_wise_sales = fields.Boolean(related='pos_config_id.show_category_wise_sales', readonly=False)
    show_taxes_detail = fields.Boolean(related='pos_config_id.show_taxes_detail', readonly=False)
    show_pricelist_detail = fields.Boolean(related='pos_config_id.show_pricelist_detail', readonly=False)
    show_payment_detail = fields.Boolean(related='pos_config_id.show_payment_detail', readonly=False)
    show_cash_in_out_details = fields.Boolean(related='pos_config_id.show_cash_in_out_details', readonly=False)

class PosSession(models.Model):
    _inherit = 'pos.session'
    
    def action_session_z_report(self):
        return self.env.ref('pos_session_z_report_ext_omax.action_report_session_z').report_action(self)
    
    def get_current_datetime(self):
        current = fields.datetime.now()
        return current.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        
    def get_opened_date(self):
        return datetime.datetime.strptime(str(self.start_at), DEFAULT_SERVER_DATETIME_FORMAT)
        
    def get_closed_date(self):
        if self.stop_at:
            return datetime.datetime.strptime(str(self.stop_at), DEFAULT_SERVER_DATETIME_FORMAT)

    def get_product_variant_wise_sale(self):
        pos_order_ids = self.env['pos.order'].search([('session_id', '=', self.id)])
        result = {}
        if self.config_id.product_or_variant == 'product':
            for pos_order in pos_order_ids:
                for line in pos_order.lines:
                    if line.product_id.product_tmpl_id.name in result:
                        result[line.product_id.product_tmpl_id.name] += line.qty
                    else:
                        result.update({line.product_id.product_tmpl_id.name: line.qty})

        if self.config_id.product_or_variant == 'variant':
            for pos_order in pos_order_ids:
                for line in pos_order.lines:
                    if line.product_id.display_name in result:
                        result[line.product_id.display_name] += line.qty
                    else:
                        result.update({line.product_id.display_name: line.qty})
        return result.items()
        
    def get_session_amount_data(self):
        pos_order_ids = self.env['pos.order'].search([('session_id', '=', self.id)])
        discount_amount = 0.0
        taxes_amount = 0.0
        total_sale_amount = 0.0
        total_gross_amount = 0.0
        total_sale_product = 0.0##
        sold_product = {}
        for pos_order in pos_order_ids:
            currency = pos_order.session_id.currency_id
            total_gross_amount += pos_order.amount_total
            for line in pos_order.lines:
                ####
                total_sale_product += line.qty##
                ####
                if line.product_id.pos_categ_ids:
                    for pos_categ_id in line.product_id.pos_categ_ids:
                        if pos_categ_id.name in sold_product:
                            sold_product[pos_categ_id.name] += line.qty
                        else:
                            sold_product.update({pos_categ_id.name: line.qty})
                else:
                    if 'undefine' in sold_product:
                        sold_product['undefine'] += line.qty
                    else:
                        sold_product.update({'undefine': line.qty})  
                """if line.product_id.pos_categ_id and line.product_id.pos_categ_id.name:
                    if line.product_id.pos_categ_id.name in sold_product:
                        sold_product[line.product_id.pos_categ_id.name] += line.qty
                    else:
                        sold_product.update({line.product_id.pos_categ_id.name: line.qty})
                else:
                    if 'undefine' in sold_product:
                        sold_product['undefine'] += line.qty
                    else:
                        sold_product.update({'undefine': line.qty})"""
                if line.tax_ids_after_fiscal_position:
                    line_taxes = line.tax_ids_after_fiscal_position.compute_all(line.price_unit * (1 - (line.discount or 0.0) / 100.0), currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
                    for tax in line_taxes['taxes']:
                        taxes_amount += tax.get('amount', 0)
                if line.discount > 0:
                    discount_amount += (((line.price_unit * line.qty) * line.discount) / 100)
                if line.qty > 0:
                    total_sale_amount += line.price_unit * line.qty
        #print("sold_product===>>>",sold_product, total_sale_product)
        return {
            'total_sale': total_sale_amount,
            'discount': discount_amount,
            'tax': taxes_amount,
            'products_sold': sold_product,
            'total_gross': total_gross_amount - taxes_amount - discount_amount,
            'final_total': total_gross_amount,
            'total_sale_product': total_sale_product,##
        }
    
    def get_taxes_data(self):
        order_ids = self.env['pos.order'].search([('session_id', '=', self.id)])
        taxes = {}
        for order in order_ids:
            currency = order.pricelist_id.currency_id
            for line in order.lines:
                if line.tax_ids_after_fiscal_position:
                    for tax in line.tax_ids_after_fiscal_position:
                        discount_amount = 0
                        if line.discount > 0:
                            discount_amount = ((line.qty*line.price_unit)* line.discount) / 100
                        untaxed_amount = (line.qty*line.price_unit) - discount_amount
                        tax_amount = ((untaxed_amount * tax.amount) / 100)
                        if tax.name:
                            if tax.name in taxes:
                                taxes[tax.name] += tax_amount
                            else:
                                taxes.update({tax.name : tax_amount})
                        else:
                            if 'undefine' in taxes:
                                taxes['undefine'] += tax_amount
                            else:
                                taxes.update({'undefine': tax_amount})
        return taxes    
    
    
    def get_pricelist(self):
        pos_order_ids = self.env['pos.order'].search([('session_id', '=', self.id)])
        pricelist = {}
        for pos_order in pos_order_ids:
            if pos_order.pricelist_id.name:
                if pos_order.pricelist_id.name in pricelist:
                    pricelist[pos_order.pricelist_id.name] += pos_order.amount_total
                else:
                    pricelist.update({pos_order.pricelist_id.name : pos_order.amount_total})
            else:
                if 'undefine' in pricelist:
                    pricelist['undefine'] += pos_order.amount_total
                else:
                    pricelist.update({'undefine': pos_order.amount_total})
        return pricelist
        
    def get_pricelist_qty(self, pricelist):
        if pricelist:
            qty_pricelist = 0
            pricelist_obj = self.env['product.pricelist'].search([('name','=', str(pricelist))])
            if pricelist_obj:
                pos_order_ids = self.env['pos.order'].search([('session_id', '=', self.id),('pricelist_id.id','=',pricelist_obj.id)])
                qty_pricelist = len(pos_order_ids)
            else:
                if pricelist == 'undefine':
                    pos_order_ids = self.env['pos.order'].search([('session_id', '=', self.id),('pricelist_id','=',False)])
                    qty_pricelist = len(pos_order_ids)
            return int(qty_pricelist)
            
    def get_payment_data(self):
        pos_payment_ids = self.env["pos.payment"].search([('session_id', '=', self.id)]).ids
        if pos_payment_ids:
            self.env.cr.execute("""
                SELECT ppm.name, sum(amount) total
                FROM pos_payment AS pp,
                     pos_payment_method AS ppm
                WHERE pp.payment_method_id = ppm.id
                AND pp.id IN %s
                GROUP BY ppm.name;
            """, (tuple(pos_payment_ids),))
            payments = self.env.cr.dictfetchall()
        else:
            payments = []
        #add tri
        for payment in payments:
            for key, value in payment.items():
                if key == 'name':
                    if self.env.user.lang in list(value.keys()):
                        payment.update({'name':value[self.env.user.lang]})
                    else:
                        for k, v in value.items():
                            payment.update({'name':v})
        return payments
        
    def get_payment_qty(self, payment_method):
        qty_payment_method = 0
        if payment_method:
            orders = self.env['pos.order'].search([('session_id', '=', self.id)])
            st_line_obj = self.env["account.bank.statement.line"].search([('pos_statement_id', 'in', orders.ids)])
            if len(st_line_obj) > 0:
                res = []
                for line in st_line_obj:
                    res.append(line.journal_id.name)
                res_dict = ast.literal_eval(json.dumps(dict(Counter(res))))
                if payment_method in res_dict:
                    qty_payment_method = res_dict[payment_method]
        return int(qty_payment_method)

