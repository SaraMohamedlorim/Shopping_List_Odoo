odoo.define('shopping_list.Dashboard', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var rpc = require('web.rpc');

var ShoppingDashboard = AbstractAction.extend({
    template: 'shopping_list.DashboardTemplate',
    events: {
        'click .o_shopping_refresh': '_onRefresh',
        'click .o_shopping_new_list': '_onNewList',
        'click .o_shopping_budget_report': '_onBudgetReport',
        'click .o_shopping_update_prices': '_onUpdatePrices',
    },

    init: function (parent, action) {
        this._super(parent, action);
        this.data = {};
    },

    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self._loadData().then(self._renderDashboard.bind(self));
        });
    },

    _loadData: function () {
        var self = this;
        return rpc.query({
            model: 'shopping.list',
            method: 'get_dashboard_data',
        }).then(function (result) {
            self.data = result;
        });
    },

    _onRefresh: function () {
        this._loadData().then(this._renderDashboard.bind(this));
    },

    _onNewList: function () {
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: 'shopping.list',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'current',
        });
    },

    _onBudgetReport: function () {
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: 'shopping.budget.report.wizard',
            view_mode: 'form',
            target: 'new',
        });
    },

    _onUpdatePrices: function () {
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: 'shopping.update.prices.wizard',
            view_mode: 'form',
            target: 'new',
        });
    },

    _renderDashboard: function () {
        this._renderStatsCards();
        this._renderCharts();
        this._renderRecentLists();
    },

    _renderStatsCards: function () {
        if (this.data) {
            this.$('.total-lists').text(this.data.total_lists || 0);
            this.$('.bought-items').text(this.data.bought_items || 0);
            this.$('.used-budget').text(this._formatAmount(this.data.used_budget || 0));
            this.$('.avg-completion').text((this.data.avg_completion || 0).toFixed(1) + '%');
        }
    },

    _renderCharts: function () {
        if (typeof Chart !== 'undefined' && this.data) {
            this._renderCompletionChart();
            this._renderCategoryChart();
            this._renderPriorityChart();
        }
    },

    _renderCompletionChart: function () {
        var ctx = this.$('#completionChart')[0];
        if (ctx && this.data.recent_lists) {
            var labels = this.data.recent_lists.map(function(list) { 
                return list.name.length > 15 ? list.name.substring(0, 15) + '...' : list.name; 
            });
            var data = this.data.recent_lists.map(function(list) { return list.completion_rate || 0; });
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Completion Rate %',
                        data: data,
                        backgroundColor: 'rgba(78, 115, 223, 0.5)',
                        borderColor: 'rgba(78, 115, 223, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });
        }
    },

    _renderCategoryChart: function () {
        var ctx = this.$('#categoryChart')[0];
        if (ctx && this.data.category_stats) {
            var labels = Object.keys(this.data.category_stats);
            var data = Object.values(this.data.category_stats);
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                        ]
                    }]
                }
            });
        }
    },

    _renderPriorityChart: function () {
        var ctx = this.$('#priorityChart')[0];
        if (ctx && this.data.priority_stats) {
            new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: ['High', 'Medium', 'Low'],
                    datasets: [{
                        data: [
                            this.data.priority_stats.high || 0,
                            this.data.priority_stats.medium || 0,
                            this.data.priority_stats.low || 0
                        ],
                        backgroundColor: ['#FF6384', '#FFCE56', '#36A2EB']
                    }]
                }
            });
        }
    },

    _renderRecentLists: function () {
        var container = this.$('.recent-lists-container');
        if (container.length && this.data.recent_lists) {
            var html = '';
            this.data.recent_lists.forEach(function(list) {
                var badgeClass = list.state === 'completed' ? 'badge-success' : 
                               list.state === 'in_progress' ? 'badge-warning' : 'badge-secondary';
                var progressClass = list.completion_rate === 100 ? 'bg-success' : 'bg-info';
                
                html += '<div class="mb-3">' +
                    '<div class="d-flex justify-content-between">' +
                    '<span class="font-weight-bold">' + list.name + '</span>' +
                    '<span class="badge ' + badgeClass + '">' + list.state + '</span>' +
                    '</div>' +
                    '<div class="progress mt-1">' +
                    '<div class="progress-bar ' + progressClass + '" style="width: ' + list.completion_rate + '%;">' +
                    list.completion_rate.toFixed(1) + '%</div>' +
                    '</div>' +
                    '</div>';
            });
            container.html(html);
        }
    },

    _formatAmount: function(amount) {
        return '$' + parseFloat(amount).toFixed(2);
    }
});

core.action_registry.add('shopping_dashboard', ShoppingDashboard);

return ShoppingDashboard;
});