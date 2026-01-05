from odoo import models, fields, api


class UpdatePrices(models.TransientModel):
    _name = 'shopping.update.prices.wizard'
    _description = 'Update item prices'

    percentage = fields.Float(string='Percentage(%)', required=True)
    operation = fields.Selection([
        ('increase', 'Increase'),
        ('decrease', 'Decrease')
    ], string='Process', required=True, default='increase')
    category_id = fields.Many2one('shopping.category', string='Category (optional)')

    def action_update_prices(self):
        self.ensure_one()
        domain = [('bought', '=', False)]
        if self.category_id:
            domain.append(('category_id', '=', self.category_id.id))

        items = self.env['shopping.item'].search(domain)

        for item in items:
            if item.estimated_price:
                if self.operation == 'increase':
                    new_price = item.estimated_price * (1 + self.percentage / 100)
                else:
                    new_price = item.estimated_price * (1 - self.percentage / 100)
                item.estimated_price = new_price

        return {'type': 'ir.actions.act_window_close'}