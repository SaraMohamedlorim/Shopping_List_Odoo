from odoo import models, fields, api
from datetime import datetime, timedelta


class ShoppingAnalyticsWizard(models.TransientModel):
    _name = 'shopping.analytics.wizard'
    _description = 'Analytics and Reporting Processor'
    report_type = fields.Selection([
        ('spending', 'spend analysis'),
        ('completion', 'Analysis of achievement'),
        ('efficiency', 'Efficiency analysis'),
        ('comparison', 'Comparing periods')
    ], string='Report type', required=True, default='spending')

    # نطاق التاريخ
    date_range = fields.Selection([
        ('week', 'Week'),
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year'),
        ('custom', 'Custom')
    ], string='Date range', default='month')
    start_date = fields.Date(string='From Date', default=fields.Date.today)
    end_date = fields.Date(string=' To Date', default=fields.Date.today)

    # التصفية
    category_id = fields.Many2one('shopping.category', string='Category')
    user_id = fields.Many2one('res.users', string='user')
    include_bought = fields.Boolean(string='Include purchased items', default=True)
    include_pending = fields.Boolean(string='Including the suspended one', default=True)

    # خيارات التقرير
    group_by_category = fields.Boolean(string='Grouped by category', default=True)
    group_by_month = fields.Boolean(string='Grouped by month', default=False)
    show_trends = fields.Boolean(string='View directions', default=True)

    @api.onchange('date_range')
    def _onchange_date_range(self):
        """تحديث تواريخ البدء والانتهاء بناءً على النطاق"""
        today = fields.Date.today()
        if self.date_range == 'week':
            self.start_date = today - timedelta(days=today.weekday())
            self.end_date = self.start_date + timedelta(days=6)
        elif self.date_range == 'month':
            self.start_date = today.replace(day=1)
            next_month = self.start_date.replace(day=28) + timedelta(days=4)
            self.end_date = next_month - timedelta(days=next_month.day)
        elif self.date_range == 'quarter':
            quarter_start = today.month - (today.month - 1) % 3
            self.start_date = today.replace(month=quarter_start, day=1)
            self.end_date = self.start_date + timedelta(days=89)
        elif self.date_range == 'year':
            self.start_date = today.replace(month=1, day=1)
            self.end_date = today.replace(month=12, day=31)

    def action_generate_report(self):
        """إنشاء التقرير"""
        self.ensure_one()

        # جمع البيانات
        data = self._collect_data()

        # إنشاء التقرير
        return self._generate_report_action(data)

    def _collect_data(self):
        """جمع البيانات للتحليل"""
        domain = [
            ('date_bought', '>=', self.start_date),
            ('date_bought', '<=', self.end_date),
        ]

        if self.category_id:
            domain.append(('category_id', '=', self.category_id.id))

        if self.user_id:
            domain.append(('list_id.user_id', '=', self.user_id.id))

        items = self.env['shopping.item'].search(domain)

        # تحضير البيانات الأساسية
        data = {
            'total_items': len(items),
            'bought_items': len(items.filtered(lambda x: x.bought)),
            'total_spent': sum(items.filtered(lambda x: x.bought).mapped('total_actual')),
            'total_estimated': sum(items.mapped('total_estimated')),
            'start_date': self.start_date,
            'end_date': self.end_date,
            'report_type': self.report_type,
        }

        # تجميع البيانات حسب الفئة
        if self.group_by_category:
            category_data = {}
            for item in items:
                category_name = item.category_id.name if item.category_id else 'Unrated'
                if category_name not in category_data:
                    category_data[category_name] = {
                        'count': 0,
                        'bought_count': 0,
                        'total_spent': 0.0,
                        'total_estimated': 0.0,
                    }

                category_data[category_name]['count'] += 1
                category_data[category_name]['total_estimated'] += item.total_estimated

                if item.bought:
                    category_data[category_name]['bought_count'] += 1
                    category_data[category_name]['total_spent'] += item.total_actual

            data['category_data'] = category_data

        return data

    def _generate_report_action(self, data):
        """إنشاء إجراء لعرض التقرير"""
        # في بيئة حقيقية، يمكن إنشاء تقرير PDF أو عرض في واجهة مخصصة
        # هنا سنعرض بيانات بسيطة

        message = """
        Analysis Report - {}
        Period: {} to {}
        ----------------------------
        Total items: {}
        Purchased items: {}
        Completion rate: {:.1f}%
        Total spent: {:.2f}
        Total estimated: {:.2f}
        """.format(
            self.report_type,
            data['start_date'],
            data['end_date'],
            data['total_items'],
            data['bought_items'],
            (data['bought_items'] / data['total_items'] * 100) if data['total_items'] > 0 else 0,
            data['total_spent'],
            data['total_estimated']
        )



        if 'category_data' in data:
           message += "\nDetails by category:\n"

        for category, stats in data['category_data'].items():
            completion_rate = (stats['bought_count'] / stats['count'] * 100) if stats['count'] > 0 else 0
            message += "- {}: {}/{} ({:.1f}%) - {:.2f}\n".format(category, stats['bought_count'], stats['count'], completion_rate, stats['total_spent'])

        # في التطبيق الحقيقي، يمكن إرجاع إجراء لعرض التقرير في نافذة أو صفحة ويب
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Report result',
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }