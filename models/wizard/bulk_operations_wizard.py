from odoo import models, fields, api
from odoo.exceptions import UserError


class BulkOperationsWizard(models.TransientModel):
    _name = 'shopping.bulk.operations.wizard'
    _description = 'Combined Processing (CPP)'

    operation_type = fields.Selection([
        ('update_status', 'Update purchase status'),
        ('update_category', 'Update category'),
        ('update_priority', 'Update priority'),
        ('delete', 'Delete items'),
        ('archive', 'Archiving items')
    ], string='Operation type', required=True, default='update_status')

    # تحديث الحالة
    new_bought_status = fields.Boolean(string='Purchased')

    # تحديث الفئة
    new_category_id = fields.Many2one('shopping.category', string='The new category')

    # تحديث الأولوية
    new_priority = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low')
    ], string='The new priority')

    # نطاق التطبيق
    apply_to = fields.Selection([
        ('selected', 'Specified items only'),
        ('list', 'All items on the list'),
        ('all', 'All items')
    ], string='apply to', default='selected')
    target_list_id = fields.Many2one('shopping.list', string='Target list')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        # إذا تم استدعاء من قائمة محددة
        if self._context.get('active_model') == 'shopping.list' and self._context.get('active_id'):
            res['apply_to'] = 'list'
            res['target_list_id'] = self._context['active_id']
        return res

    def action_execute_operation(self):
        """تنفيذ العملية المجمعة"""
        self.ensure_one()

        # الحصول على العناصر المستهدفة
        items = self._get_target_items()

        if not items:
            raise UserError("No items match the search criteria")

        # تنفيذ العملية
        if self.operation_type == 'update_status':
            updated = self._update_bought_status(items)
            message = "Status of {} items has been updated".format(updated)
        elif self.operation_type == 'update_category':
            updated = self._update_category(items)
            message = "Category of {} items has been updated".format(updated)
        elif self.operation_type == 'update_priority':
            updated = self._update_priority(items)
            message = "Priority of {} items has been updated".format(updated)
        elif self.operation_type == 'delete':
            deleted = self._delete_items(items)
            message =  "{} items have been deleted".format(deleted)
        else:  # archive
            archived = self._archive_items(items)
            message = "{} items have been archived".format(archived)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success of the operation',
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def _get_target_items(self):
        """الحصول على العناصر المستهدفة"""
        domain = []

        if self.apply_to == 'selected':
            # العناصر المحددة في السياق
            if self._context.get('active_model') == 'shopping.item' and self._context.get('active_ids'):
                domain.append(('id', 'in', self._context['active_ids']))
            else:
                return self.env['shopping.item']
        elif self.apply_to == 'list':
            if self.target_list_id:
                domain.append(('list_id', '=', self.target_list_id.id))
            else:
                raise UserError("يرجى تحديد قائمة مستهدفة")
        # else: 'all' - لا توجد قيود إضافية

        return self.env['shopping.item'].search(domain)

    def _update_bought_status(self, items):
        """تحديث حالة الشراء"""
        items_to_update = items.filtered(lambda x: x.bought != self.new_bought_status)
        items_to_update.write({
            'bought': self.new_bought_status,
            'date_bought': fields.Datetime.now() if self.new_bought_status else False
        })
        return len(items_to_update)

    def _update_category(self, items):
        """تحديث الفئة"""
        items_to_update = items.filtered(lambda x: x.category_id != self.new_category_id)
        items_to_update.write({'category_id': self.new_category_id.id})
        return len(items_to_update)

    def _update_priority(self, items):
        """تحديث الأولوية"""
        items_to_update = items.filtered(lambda x: x.priority != self.new_priority)
        items_to_update.write({'priority': self.new_priority})
        return len(items_to_update)

    def _delete_items(self, items):
        """حذف العناصر"""
        count = len(items)
        items.unlink()
        return count

    def _archive_items(self, items):
        """أرشفة العناصر (تحديث حالة القائمة)"""
        # في هذا المثال، نقوم بتحديث حالة العنصر إلى "مكتمل"
        items_to_update = items.filtered(lambda x: not x.bought)
        items_to_update.write({'bought': True})
        return len(items_to_update)