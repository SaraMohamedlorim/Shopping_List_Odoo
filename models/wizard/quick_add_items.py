from odoo import models, fields, api
from odoo.exceptions import UserError

class QuickAddItems(models.TransientModel):
    _name = 'shopping.quick.add.items.wizard'
    _description = 'Add quick elements'

    list_id = fields.Many2one('shopping.list', string='Shopping list', required=True)
    item_lines = fields.One2many('quick.add.items.line', 'wizard_id', string='Items')

    def action_add_items(self):
        for wizard in self:
            for line in wizard.item_lines:
                if line.name:
                    self.env['shopping.item'].create({
                        'name': line.name,
                        'quantity': line.quantity,
                        'uom': line.uom,
                        'category_id': line.category_id.id,
                        'priority': line.priority,
                        'estimated_price': line.estimated_price,
                        'list_id': wizard.list_id.id,
                    })
        return {'type': 'ir.actions.act_window_close'}

class QuickAddItemsLine(models.TransientModel):
    _name = 'quick.add.items.line'
    _description = 'Quick element addition line'

    wizard_id = fields.Many2one('quick.add.items.wizard', string='Wizard')
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
    estimated_price = fields.Float(string='Estimated price')