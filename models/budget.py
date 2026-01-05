from odoo import models, fields, api
from datetime import datetime , timedelta


class ShoppingBudget(models.Model):
    _name = 'shopping.budget'
    _description = 'Shopping budget'

    name = fields.Char(string='budget name', required=True)
    user_id = fields.Many2one('res.users', string='user', default=lambda self: self.env.user)
    period = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ], string='period', required=True)

    amount = fields.Float(string='Amount', required=True)
    start_date = fields.Date(string='start date', required=True)
    end_date = fields.Date(string=' end date', required=True)

    category_id = fields.Many2one('shopping.category', string='Category')
    actual_spent = fields.Float(string='Actual Spent', compute='_compute_actual_spent')
    remaining = fields.Float(string='Remaning', compute='_compute_actual_spent')
    usage_percentage = fields.Float(string='usage percentage', compute='_compute_actual_spent')

    @api.depends('amount', 'category_id', 'start_date', 'end_date')
    def _compute_actual_spent(self):
        for record in self:
            domain = [
                ('bought', '=', True),
                ('date_bought', '>=', record.start_date),
                ('date_bought', '<=', record.end_date)
            ]
            if record.category_id:
                domain.append(('category_id', '=', record.category_id.id))

            items = self.env['shopping.item'].search(domain)
            record.actual_spent = sum(items.mapped('total_actual'))
            record.remaining = record.amount - record.actual_spent
            record.usage_percentage = (record.actual_spent / record.amount * 100) if record.amount > 0 else 0

    @api.model
    def create_monthly_budgets(self):
        """إنشاء ميزانيات شهرية تلقائية"""
        current_month = datetime.now().replace(day=1)
        next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)

        categories = self.env['shopping.category'].search([])
        for category in categories:
            existing = self.search([
                ('category_id', '=', category.id),
                ('start_date', '=', current_month),
                ('period', '=', 'monthly')
            ])
            if not existing:
                self.create({
                    'name': "Budget {} For Month {}".format(category.name, current_month.strftime('%B %Y')),
                    'category_id': category.id,
                    'period': 'monthly',
                    'amount': 1000,  # قيمة افتراضية
                    'start_date': current_month,
                    'end_date': next_month - timedelta(days=1)
                })