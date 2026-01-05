from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class ShoppingList(models.Model):
    _name = 'shopping.list'
    _description = 'shopping list'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='list name', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='user', default=lambda self: self.env.user)
    date_created = fields.Datetime(string='Date of Creation', default=fields.Datetime.now)
    state = fields.Selection([
        ('draft', 'Darft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='state', default='draft', tracking=True)

    item_ids = fields.One2many('shopping.item', 'list_id', string='Items')
    total_items = fields.Integer(string='total items', compute='_compute_totals')
    completed_items = fields.Integer(string='Completed elements', compute='_compute_totals')
    completion_rate = fields.Float(string='Completion rate', compute='_compute_totals')

    total_budget = fields.Float(string='Total budget', compute='_compute_budget')
    actual_spent = fields.Float(string='Actual expenditure', compute='_compute_budget')
    budget_variance = fields.Float(string='variance', compute='_compute_budget')

    notes = fields.Text(string='notes')
    color = fields.Integer(string='mark color')

    @api.depends('item_ids', 'item_ids.bought')
    def _compute_totals(self):
        for record in self:
            record.total_items = len(record.item_ids)
            record.completed_items = len(record.item_ids.filtered(lambda x: x.bought))
            record.completion_rate = (
                        record.completed_items / record.total_items * 100) if record.total_items > 0 else 0

    @api.depends('item_ids', 'item_ids.estimated_price', 'item_ids.bought')
    def _compute_budget(self):
        for record in self:
            record.total_budget = sum(record.item_ids.mapped('estimated_price'))
            record.actual_spent = sum(record.item_ids.filtered(lambda x: x.bought).mapped('estimated_price'))
            record.budget_variance = record.total_budget - record.actual_spent

    def action_mark_in_progress(self):
        self.write({'state': 'in_progress'})

    def action_mark_completed(self):
        self.write({'state': 'completed'})

    def action_mark_cancelled(self):
        self.write({'state': 'cancelled'})

    def action_duplicate_list(self):
        for record in self:
            new_list = record.copy(default={
                'name': "{} (copy)".format(record.name),
                'state': 'draft'
            })
            # نسخ العناصر
            for item in record.item_ids:
                item.copy(default={
                    'list_id': new_list.id,
                    'bought': False
                })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'shopping.list',
            'res_id': new_list.id,
            'view_mode': 'form',
            'target': 'current',
        }