from odoo import models, fields, api
from odoo import http
from odoo.http import request
import json
from datetime import datetime, timedelta


class ShoppingDashboard(http.Controller):

    @http.route('/shopping/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self):
        """الحصول على بيانات لوحة التحكم"""
        ShoppingList = request.env['shopping.list']
        ShoppingItem = request.env['shopping.item']
        ShoppingBudget = request.env['shopping.budget']

        # الإحصائيات الأساسية
        total_lists = ShoppingList.search_count([('user_id', '=', request.env.uid)])
        bought_items = ShoppingItem.search_count([
            ('user_id', '=', request.env.uid),
            ('bought', '=', True)
        ])

        # حساب الميزانية المستخدمة
        bought_items_records = ShoppingItem.search([
            ('user_id', '=', request.env.uid),
            ('bought', '=', True)
        ])
        used_budget = sum(bought_items_records.mapped('total_actual'))

        # متوسط الإنجاز
        user_lists = ShoppingList.search([('user_id', '=', request.env.uid)])
        avg_completion = sum(user_lists.mapped('completion_rate')) / len(user_lists) if user_lists else 0

        # القوائم الحديثة
        recent_lists = ShoppingList.search([
            ('user_id', '=', request.env.uid)
        ], limit=5, order='create_date desc')

        recent_lists_data = []
        for lst in recent_lists:
            recent_lists_data.append({
                'name': lst.name,
                'state': lst.state,
                'completion_rate': lst.completion_rate
            })

        # إحصائيات الميزانية
        current_budgets = ShoppingBudget.search([
            ('user_id', '=', request.env.uid),
            ('start_date', '<=', fields.Date.today()),
            ('end_date', '>=', fields.Date.today())
        ])

        total_budget = sum(current_budgets.mapped('amount'))
        budget_used = sum(current_budgets.mapped('actual_spent'))
        budget_remaining = total_budget - budget_used

        # العناصر حسب الأولوية
        priority_stats = {
            'high': ShoppingItem.search_count([
                ('list_id.user_id', '=', request.env.uid),
                ('priority', '=', 'high')
            ]),
            'medium': ShoppingItem.search_count([
                ('list_id.user_id', '=', request.env.uid),
                ('priority', '=', 'medium')
            ]),
            'low': ShoppingItem.search_count([
                ('list_id.user_id', '=', request.env.uid),
                ('priority', '=', 'low')
            ])
        }

        # العناصر حسب الفئة
        category_stats = {}
        categories = request.env['shopping.category'].search([])
        for category in categories:
            count = ShoppingItem.search_count([
                ('list_id.user_id', '=', request.env.uid),
                ('category_id', '=', category.id)
            ])
            if count > 0:
                category_stats[category.name] = count

        return {
            'total_lists': total_lists,
            'bought_items': bought_items,
            'used_budget': used_budget,
            'avg_completion': avg_completion,
            'recent_lists': [{
                'name': lst.name,
                'state': lst.state,
                'completion_rate': lst.completion_rate
            } for lst in recent_lists]
        }

    @http.route('/shopping/dashboard', type='http', auth='user', website=True)
    def shopping_dashboard(self, **kwargs):
        """عرض لوحة التحكم"""
        # يمكنك استخدام هذا المسار إذا أردت عرض لوحة التحكم في واجهة الموقع
        return request.render('shopping_list.shopping_dashboard')