from odoo import models, fields, api
from datetime import datetime, timedelta


class BudgetReport(models.TransientModel):
    _name = 'shopping.budget.report.wizard'
    _description = 'budget report'

    date_from = fields.Date(string='From Date', required=True, default=fields.Date.today)
    date_to = fields.Date(string='To Date', required=True, default=fields.Date.today)
    category_id = fields.Many2one('shopping.category', string='Category (optional)')
    group_by_category = fields.Boolean(string='Grouped by category', default=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        # افتراضيًا، تقرير عن الشهر الحالي
        today = fields.Date.today()
        first_day = today.replace(day=1)
        last_day = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        res['date_from'] = first_day
        res['date_to'] = last_day
        return res

    def action_generate_report(self):
        self.ensure_one()
        domain = [
            ('bought', '=', True),
            ('date_bought', '>=', self.date_from),
            ('date_bought', '<=', self.date_to),
        ]

        if self.category_id:
            domain.append(('category_id', '=', self.category_id.id))

        items = self.env['shopping.item'].search(domain)

        report_data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'total_spent': sum(items.mapped('total_actual')),
            'total_items': len(items),
        }

        if self.group_by_category:
            categories = {}
            for item in items:
                category_name = item.category_id.name if item.category_id else 'Unrated'
                if category_name not in categories:
                    categories[category_name] = {'count': 0, 'amount': 0.0}
                categories[category_name]['count'] += 1
                categories[category_name]['amount'] += item.total_actual
            report_data['categories'] = categories

        message = """
        Budget report from {} To {}
        ----------------------------
        Total expense: {:.2f}
        Number of items purchased: {}
        """.format(self.date_from, self.date_to, report_data['total_spent'], report_data['total_items'])


        if self.group_by_category and 'categories' in report_data:
            message += "\nDetails by category:\n"
            for category, data in report_data['categories'].items():
                message += "- {}: {:.2f} ({} component)\n".format(category, data['amount'], data['count'])

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'budget.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': {'default_message': message},
        }

    message = fields.Text(string='Report result', readonly=True)