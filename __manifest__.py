{
    'name': 'Shopping list management system',
    'version': '16.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Integrated system for managing shopping lists and budgets',
    'description': """
        Integrated shopping list management system
        ================================

               Features:
        * Shopping list management
        * Purchase tracking
        * Budget management
        * Statistics and reports
        * Item classification
        * Priority system
        * Interactive dashboard
    """,
    'author': 'sara mohammed',
    'website': 'https://www.sara.com',
    'depends': ['base', 'web', 'mail'],

    'data': [
        'security/shopping_list_security.xml',
        'security/ir.model.access.csv',

        'data/shopping_list_data.xml',

        'views/shopping_list_views.xml',
        'views/shopping_item_views.xml',
        'views/category_views.xml',
        'views/budget_views.xml',
        'views/dashboard_views.xml',
        # 'views/dashboard_templates.xml',


        'wizards/quick_add_wizard_views.xml',
        'wizards/import_export_wizard_view.xml',
        'wizards/budget_planning_wizard_views.xml',
        'wizards/shopping_analytics_wizard_views.xml',
        'wizards/bulk_operations_wizard_views.xml',

        'wizards/quick_add_items_views.xml',
        'wizards/copy_shopping_list_views.xml',
        'wizards/update_prices_views.xml',
        'wizards/budget_report_views.xml',
    ],

    'images': ['static/description/groceries.png'],
    'icon': '/Shopping_List/static/description/groceries.png',

    'assets': {
        'web.assets_backend': [
            'Shopping_List/static/src/css/style.css',
            'Shopping_List/static/src/js/dashboard.js',
        ],
    },
    'demo': [
        'data/Shopping_List_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}