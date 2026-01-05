from odoo import models, fields, api


class CopyShoppingList(models.TransientModel):
    _name = 'shopping.copy.shopping.list.wizard'
    _description = 'Copy shopping list'

    original_list_id = fields.Many2one('shopping.list', string='Original List', required=True)
    new_list_name = fields.Char(string='Name of the new list', required=True)
    copy_items = fields.Boolean(string='Copy items', default=True)
    reset_bought_status = fields.Boolean(string='Reset Purchase Status', default=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self._context.get('active_id'):
            res['original_list_id'] = self._context['active_id']
            original_list = self.env['shopping.list'].browse(self._context['active_id'])
            res['new_list_name'] = "{} (copy)".format(original_list.name)
        return res

    def action_copy_list(self):
        self.ensure_one()
        new_list = self.original_list_id.copy(default={
            'name': self.new_list_name,
            'state': 'draft',
        })

        if self.copy_items:
            for item in self.original_list_id.item_ids:
                item.copy(default={
                    'list_id': new_list.id,
                    'bought': False if self.reset_bought_status else item.bought,
                })

        # فتح القائمة الجديدة
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'shopping.list',
            'res_id': new_list.id,
            'view_mode': 'form',
            'target': 'current',
        }