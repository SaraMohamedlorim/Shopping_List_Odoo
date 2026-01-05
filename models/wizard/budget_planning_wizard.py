from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class BudgetPlanningWizard(models.TransientModel):
    _name = 'shopping.budget.planning.wizard'
    _description = 'Budget Planning Wizard'

    planning_type = fields.Selection([
        ('monthly', ' Monthly planning'),
        ('category', 'Planning by category'),
        ('automatic', 'Auto layout')
    ], string='Layout type', required=True, default='monthly')

    # الحقول العامة
    budget_amount = fields.Float(string='Total budget', required=True)
    start_date = fields.Date(string='start date', default=fields.Date.today)
    period = fields.Selection([
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='period', default='monthly')

    # تخطيط حسب الفئة
    category_budgets = fields.One2many('shopping.category.budget.line', 'wizard_id', string='Category budgets')

    # التخطيط التلقائي
    auto_based_on = fields.Selection([
        ('history', 'Based on historical record'),
        ('average', 'Based on the monthly average')
    ], string='depending on', default='history')
    reference_months = fields.Integer(string='Reference months number' , default=3)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'category_budgets' in fields:
            # تعبئة تلقائية بالفئات الموجودة
            categories = self.env['shopping.category'].search([])
            res['category_budgets'] = [(0, 0, {
                'category_id': category.id,
                'allocated_amount': 0.0,
            }) for category in categories]
        return res

    def action_generate_budget(self):
        """إنشاء ميزانية بناءً على الإعدادات"""
        self.ensure_one()

        if self.planning_type == 'monthly':
            return self._generate_monthly_budget()
        elif self.planning_type == 'category':
            return self._generate_category_budget()
        else:
            return self._generate_automatic_budget()

    def _generate_monthly_budget(self):
        """إنشاء ميزانية شهرية"""
        budget_name = "budget {} {}".format(self.start_date.strftime('%B'), self.start_date.strftime('%Y'))

        budget = self.env['shopping.budget'].create({
            'name': budget_name,
            'amount': self.budget_amount,
            'period': self.period,
            'start_date': self.start_date,
            'end_date': self._calculate_end_date(),
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'shopping.budget',
            'res_id': budget.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _generate_category_budget(self):
        """إنشاء ميزانيات للفئات"""
        total_allocated = sum(line.allocated_amount for line in self.category_budgets)

        if abs(total_allocated - self.budget_amount) > 0.01:
            raise UserError(
                "The amount allocated to the categories ({}) Not equal to the total budget ({})".format(total_allocated, self.budget_amount))

        created_budgets = []
        for line in self.category_budgets:
            if line.allocated_amount > 0:
                budget = self.env['shopping.budget'].create({
                    'name':"budget {} - {}".format(line.category_id.name, self.start_date.strftime('%B %Y')),
                    'amount': line.allocated_amount,
                    'period': self.period,
                    'start_date': self.start_date,
                    'end_date': self._calculate_end_date(),
                    'category_id': line.category_id.id,
                })
                created_budgets.append(budget.id)

        message = "has been created {} Budget for categories".format(len(created_budgets))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Successful budget creation',
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def _generate_automatic_budget(self):
        """إنشاء ميزانية تلقائية بناءً على البيانات التاريخية"""
        # حساب متوسط الإنفاق بناءً على السجل التاريخي
        end_date = self.start_date
        start_date = end_date - timedelta(days=30 * self.reference_months)

        items = self.env['shopping.item'].search([
            ('bought', '=', True),
            ('date_bought', '>=', start_date),
            ('date_bought', '<=', end_date),
        ])

        total_spent = sum(items.mapped('total_actual'))
        average_monthly = total_spent / self.reference_months

        # اقتراح ميزانية بناءً على المتوسط
        suggested_budget = average_monthly * 1.1  # زيادة 10% عن المتوسط

        self.budget_amount = suggested_budget

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'shopping.budget.planning.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_budget_amount': suggested_budget}
        }

    def _calculate_end_date(self):
        """حساب تاريخ الانتهاء بناءً على الفترة"""
        if self.period == 'weekly':
            return self.start_date + timedelta(days=6)
        elif self.period == 'monthly':
            next_month = self.start_date.replace(day=28) + timedelta(days=4)
            return next_month - timedelta(days=next_month.day)
        elif self.period == 'quarterly':
            return self.start_date + timedelta(days=89)
        else:  # yearly
            return self.start_date.replace(year=self.start_date.year + 1) - timedelta(days=1)


class CategoryBudgetLine(models.TransientModel):
    _name = 'shopping.category.budget.line'
    _description = 'Category budget line'

    wizard_id = fields.Many2one('shopping.budget.planning.wizard', string='Processor')
    category_id = fields.Many2one('shopping.category', string='Category', required=True)
    allocated_amount = fields.Float(string='Amount allocated')
    historical_spending = fields.Float(string='Historic spending', compute='_compute_historical_spending')

    def _compute_historical_spending(self):
        """حساب الإنفاق التاريخي للفئة"""
        for record in self:
            if record.category_id:
                # حساب الإنفاق في آخر 3 أشهر
                three_months_ago = fields.Date.today() - timedelta(days=90)
                items = self.env['shopping.item'].search([
                    ('category_id', '=', record.category_id.id),
                    ('bought', '=', True),
                    ('date_bought', '>=', three_months_ago),
                ])
                record.historical_spending = sum(items.mapped('total_actual'))
            else:
                record.historical_spending = 0.0