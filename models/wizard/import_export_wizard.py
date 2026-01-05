from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import csv
import io


class ImportExportWizard(models.TransientModel):
    _name = 'shopping.import.export.wizard'
    _description = 'Import and Export Processor'

    operation_type = fields.Selection([
        ('import', 'Import from CSV'),
        ('export', 'Export to CSV'),
    ], string='Operation type', required=True, default='import')

    # حقول الاستيراد
    import_file = fields.Binary(string='CSV File', required=False)
    import_filename = fields.Char(string='File Name')
    list_id = fields.Many2one('shopping.list', string='Destination List', required=False)
    import_override = fields.Boolean(string='Replace existing data', default=False)

    # حقول التصدير
    export_list_id = fields.Many2one('shopping.list', string='export list', required=False)
    export_all_lists = fields.Boolean(string='Export all lists', default=False)
    export_include_bought = fields.Boolean(string='Include purchased items', default=True)

    @api.onchange('operation_type')
    def _onchange_operation_type(self):
        """تحديث الحقول بناءً على نوع العملية"""
        if self.operation_type == 'import':
            self.export_list_id = False
            self.export_all_lists = False
        else:
            self.import_file = False
            self.list_id = False

    def action_execute(self):
        """تنفيذ العملية المحددة"""
        self.ensure_one()
        if self.operation_type == 'import':
            return self._action_import()
        else:
            return self._action_export()

    def _action_import(self):
        """استيراد البيانات من ملف CSV"""
        if not self.import_file:
            raise UserError("Please select a file to import.")

        if not self.list_id:
            raise UserError("Please select a destination menu.")

        try:
            # فك تشفير الملف
            file_content = base64.b64decode(self.import_file).decode('utf-8')
            csv_file = io.StringIO(file_content)
            csv_reader = csv.DictReader(csv_file)

            imported_count = 0
            for row in csv_reader:
                # تحويل البيانات
                item_vals = {
                    'name': row.get('Name', '').strip(),
                    'quantity': float(row.get('Quantity', 1)),
                    'uom': row.get('Unit', 'unit'),
                    'priority': row.get('Priority', 'medium'),
                    'estimated_price': float(row.get('Estimated_Price', 0)),
                    'list_id': self.list_id.id,
                    'notes': row.get('Notes', ''),
                }

                # معالجة الفئة
                category_name = row.get('Category', '').strip()
                if category_name:
                    category = self.env['shopping.category'].search([('name', '=', category_name)], limit=1)
                    if not category:
                        category = self.env['shopping.category'].create({'name': category_name})
                    item_vals['category_id'] = category.id

                # التحقق من العنصر الموجود
                if self.import_override:
                    existing_item = self.env['shopping.item'].search([
                        ('name', '=', item_vals['name']),
                        ('list_id', '=', self.list_id.id)
                    ], limit=1)
                    if existing_item:
                        existing_item.write(item_vals)
                    else:
                        self.env['shopping.item'].create(item_vals)
                else:
                    self.env['shopping.item'].create(item_vals)

                imported_count += 1

            message = "{} items have been successfully imported to {}".format(imported_count, self.list_id.name)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Import success',
                    'message': message,
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            raise UserError("Import error: {}".format(str(e)))

    def _action_export(self):
        """تصدير البيانات إلى ملف CSV"""
        # بناء نطاق البحث
        domain = []
        if not self.export_all_lists and self.export_list_id:
            domain.append(('list_id', '=', self.export_list_id.id))

        if not self.export_include_bought:
            domain.append(('bought', '=', False))

        items = self.env['shopping.item'].search(domain)

        # إنشاء محتوى CSV
        output = io.StringIO()
        fieldnames = ['Name', 'Quantity', 'Unit', 'Category', 'Priority', 'Estimated_Price', 'Bought', 'Store', 'Notes']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for item in items:
            writer.writerow({
                'Name': item.name,
                'Quantity': item.quantity,
                'Unit': item.uom,
                'Category': item.category_id.name if item.category_id else '',
                'Priority': item.priority,
                'Estimated_Price': item.estimated_price,
                'Bought': 'Yes' if item.bought else 'No',
                'Store': item.store or '',
                'Notes': item.notes or '',
            })

        csv_content = output.getvalue()
        output.close()

        # إرجاع action للتحميل
        filename ="shopping_export_{}.csv".format(fields.Datetime.now().strftime('%Y%m%d_%H%M%S'))
        return {
            'type': 'ir.actions.act_url',
            'url':'/web/content/?model=shopping.import.export.wizard&id={}&field=export_file&filename={}&download=true'.format(self.id, filename),
            'target': 'self',
        }

    export_file = fields.Binary(string='export file', compute='_compute_export_file')

    def _compute_export_file(self):
        """حساب ملف التصدير"""
        for record in self:
            if record.operation_type == 'export':
                # إعادة تنفيذ التصدير عند الطلب
                record.export_file = base64.b64encode(self._generate_export_content().encode('utf-8'))
            else:
                record.export_file = False

    def _generate_export_content(self):
        """توليد محتوى التصدير"""
        output = io.StringIO()
        fieldnames = ['Name', 'Quantity', 'Unit', 'Category', 'Priority', 'Estimated_Price', 'Bought', 'Store', 'Notes']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        domain = []
        if not self.export_all_lists and self.export_list_id:
            domain.append(('list_id', '=', self.export_list_id.id))
        if not self.export_include_bought:
            domain.append(('bought', '=', False))

        items = self.env['shopping.item'].search(domain)

        for item in items:
            writer.writerow({
                'Name': item.name,
                'Quantity': item.quantity,
                'Unit': item.uom,
                'Category': item.category_id.name if item.category_id else '',
                'Priority': item.priority,
                'Estimated_Price': item.estimated_price,
                'Bought': 'Yes' if item.bought else 'No',
                'Store': item.store or '',
                'Notes': item.notes or '',
            })

        content = output.getvalue()
        output.close()
        return content