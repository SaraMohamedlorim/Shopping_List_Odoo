from odoo import models, fields, api

class ShoppingCategory(models.Model):
    _name = 'shopping.category'
    _description = 'Shopping category'
    _order = 'name'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'

    name = fields.Char(string='category name', required=True, translate=True)
    complete_name = fields.Char(string='full name', compute='_compute_complete_name', store=True)
    parent_id = fields.Many2one('shopping.category', string='Main category', index=True)
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('shopping.category', 'parent_id', string='Subcategories')
    color = fields.Integer(string='Color')
    description = fields.Text(string='Description')
    item_count = fields.Integer(string='number of items', compute='_compute_item_count')
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The category name must be unique!'),
    ]

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = "{} / {}".format(category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    def _compute_item_count(self):
        for category in self:
            category.item_count = self.env['shopping.item'].search_count([
                ('category_id', '=', category.id)
            ])

    def action_view_items(self):
        """عرض عناصر هذه الفئة"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Items {}'.format(self.name),
            'res_model': 'shopping.item',
            'view_mode': 'tree,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id}
        }