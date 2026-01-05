from odoo import models, fields, api


class ShoppingItem(models.Model):
    _name = 'shopping.item'
    _description = 'shopping item'
    _order = 'priority desc, create_date'

    name = fields.Char(string='item name', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    uom = fields.Selection([
        ('unit', 'Unit'),
        ('kg', 'Kg'),
        ('g', 'G'),
        ('l', 'L'),
        ('ml', 'Ml'),
        ('pack', 'Pack'),
        ('bottle', 'Bottle')
    ], string='unit of measurement', default='unit')

    category_id = fields.Many2one('shopping.category', string='Category')
    priority = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low')
    ], string='Priority', default='medium')

    estimated_price = fields.Float(string='Estimated Price')
    actual_price = fields.Float(string='Actual Price')
    store = fields.Char(string='Store')

    bought = fields.Boolean(string='Purchased', default=False)
    date_bought = fields.Datetime(string='Purchase date')

    list_id = fields.Many2one('shopping.list', string='shopping list', ondelete='cascade')
    notes = fields.Text(string='Notes')

    image = fields.Binary(string='Image')

    # الحقول المحسوبة
    total_estimated = fields.Float(string='Total Estimated', compute='_compute_totals')
    total_actual = fields.Float(string='Total Actual', compute='_compute_totals')

    @api.depends('quantity', 'estimated_price', 'actual_price')
    def _compute_totals(self):
        for record in self:
            record.total_estimated = record.quantity * (record.estimated_price or 0)
            record.total_actual = record.quantity * (record.actual_price or 0)

    def action_toggle_bought(self):
        for record in self:
            record.bought = not record.bought
            if record.bought:
                record.date_bought = fields.Datetime.now()


