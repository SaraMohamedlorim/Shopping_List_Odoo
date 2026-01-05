from odoo import models, fields, api
from odoo.exceptions import UserError


class QuickAddWizard(models.TransientModel):
    _name = 'shopping.quick.add.wizard'
    _description = 'Quick Item Add-on Wizard'

    list_id = fields.Many2one('shopping.list', string='Shopping List', required=True)
    item_lines = fields.One2many('shopping.quick.add.line', 'wizard_id', string='Items')

    # الحقول الافتراضية للعناصر الجديدة
    default_category_id = fields.Many2one('shopping.category', string='Default category')
    default_priority = fields.Selection([
        ('high', 'high'),
        ('medium', 'medium'),
        ('low', 'low')
    ], string='Default priority', default='medium')
    default_uom = fields.Selection([
        ('unit', 'Unit'),
        ('kg', 'Kg'),
        ('g', 'G'),
        ('l', 'L'),
        ('ml', 'Ml'),
        ('pack', 'Pack'),
        ('bottle', 'Bottle')
    ], string='Default unit of measurement', default='unit')

    @api.model
    def default_get(self, fields):
        # ✅ التصحيح: استدعاء super() بشكل صحيح
        res = super(QuickAddWizard, self).default_get(fields)

        # إذا تم استدعاء الويزارد من قائمة محددة
        if self._context.get('active_id') and self._context.get('active_model') == 'shopping.list':
            res['list_id'] = self._context['active_id']

        # تعبئة تلقائية بخطوط فارغة للإضافة السريعة
        if 'item_lines' in fields and 'item_lines' not in res:
            res['item_lines'] = [(0, 0, {'name': '', 'quantity': 1.0})]

        return res

    def action_add_items(self):
        """إضافة العناصر إلى قائمة التسوق"""
        self.ensure_one()
        if not self.item_lines:
           raise UserError("Please add at least one item")

        created_items = []
        for line in self.item_lines:
            item_vals = {
                'name': line.name,
                'quantity': line.quantity,
                'uom': line.uom or self.default_uom,
                'category_id': line.category_id.id or self.default_category_id.id,
                'priority': line.priority or self.default_priority,
                'estimated_price': line.estimated_price,
                'list_id': self.list_id.id,
                'notes': line.notes,
            }
            item = self.env['shopping.item'].create(item_vals)
            created_items.append(item.id)

        # عرض رسالة نجاح
        message = "{} items have been successfully added to the list {}".format(len(created_items), self.list_id.name)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'shopping.list',
            'res_id': self.list_id.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'create': False},
        }

    def action_add_another(self):
        """إضافة عناصر أخرى مع الحفاظ على الإعدادات"""
        self.ensure_one()
        self.item_lines = [(5, 0, 0)]  # مسح العناصر الحالية
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'shopping.quick.add.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class QuickAddLine(models.TransientModel):
    _name = 'shopping.quick.add.line'
    _description = 'Quick Add Line'

    wizard_id = fields.Many2one('shopping.quick.add.wizard', string='Processor')
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
    ], string='unit of measurement')
    category_id = fields.Many2one('shopping.category', string='Category')
    priority = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low')
    ], string='Priority')
    estimated_price = fields.Float(string='Estimated price')
    notes = fields.Text(string='notes')