/**
 * Chart.js Integration for Face-ID Attendance System
 * Handles dashboard charts, attendance statistics, and data visualization
 */

/**
 * Chart Manager Class
 */
class ChartManager {
    constructor() {
        this.charts = new Map();
        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#fff',
                    borderWidth: 1,
                    cornerRadius: 6
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            }
        };
    }

    /**
     * Create attendance overview chart (pie chart)
     */
    createAttendanceOverview(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const config = {
            type: 'pie',
            data: {
                labels: ['Có mặt', 'Vắng mặt', 'Muộn', 'Có phép'],
                datasets: [{
                    data: [
                        data.present || 0,
                        data.absent || 0,
                        data.late || 0,
                        data.excused || 0
                    ],
                    backgroundColor: [
                        '#28a745',  // Present - Green
                        '#dc3545',  // Absent - Red
                        '#ffc107',  // Late - Yellow
                        '#17a2b8'   // Excused - Cyan
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        ...this.defaultOptions.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        };

        const chart = new Chart(canvas, config);
        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create daily attendance chart (line chart)
     */
    createDailyAttendanceChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const config = {
            type: 'line',
            data: {
                labels: data.dates || [],
                datasets: [{
                    label: 'Có mặt',
                    data: data.present || [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Vắng mặt',
                    data: data.absent || [],
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        title: {
                            display: true,
                            text: 'Số học sinh'
                        }
                    },
                    x: {
                        ...this.defaultOptions.scales.x,
                        title: {
                            display: true,
                            text: 'Ngày'
                        }
                    }
                }
            }
        };

        const chart = new Chart(canvas, config);
        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create class attendance comparison (bar chart)
     */
    createClassComparisonChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const config = {
            type: 'bar',
            data: {
                labels: data.classes || [],
                datasets: [{
                    label: 'Tỷ lệ có mặt (%)',
                    data: data.attendance_rates || [],
                    backgroundColor: [
                        '#007bff', '#28a745', '#17a2b8', '#ffc107',
                        '#fd7e14', '#e83e8c', '#6f42c1', '#6c757d'
                    ],
                    borderColor: [
                        '#0056b3', '#1e7e34', '#117a8b', '#d39e00',
                        '#dc5404', '#d91a72', '#5a32a3', '#545b62'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Tỷ lệ (%)'
                        }
                    },
                    x: {
                        ...this.defaultOptions.scales.x,
                        title: {
                            display: true,
                            text: 'Lớp học'
                        }
                    }
                },
                plugins: {
                    ...this.defaultOptions.plugins,
                    tooltip: {
                        ...this.defaultOptions.plugins.tooltip,
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        };

        const chart = new Chart(canvas, config);
        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create monthly attendance trend (area chart)
     */
    createMonthlyTrendChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const config = {
            type: 'line',
            data: {
                labels: data.months || [],
                datasets: [{
                    label: 'Tỷ lệ có mặt (%)',
                    data: data.attendance_rates || [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#007bff',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        min: 0,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Tỷ lệ có mặt (%)'
                        }
                    },
                    x: {
                        ...this.defaultOptions.scales.x,
                        title: {
                            display: true,
                            text: 'Tháng'
                        }
                    }
                }
            }
        };

        const chart = new Chart(canvas, config);
        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create attendance by time slot (stacked bar chart)
     */
    createTimeSlotChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const config = {
            type: 'bar',
            data: {
                labels: data.time_slots || [],
                datasets: [{
                    label: 'Có mặt',
                    data: data.present || [],
                    backgroundColor: '#28a745',
                    borderColor: '#1e7e34',
                    borderWidth: 1
                }, {
                    label: 'Muộn',
                    data: data.late || [],
                    backgroundColor: '#ffc107',
                    borderColor: '#d39e00',
                    borderWidth: 1
                }, {
                    label: 'Vắng mặt',
                    data: data.absent || [],
                    backgroundColor: '#dc3545',
                    borderColor: '#c82333',
                    borderWidth: 1
                }]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    x: {
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Khung giờ'
                        }
                    },
                    y: {
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Số học sinh'
                        }
                    }
                }
            }
        };

        const chart = new Chart(canvas, config);
        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Update chart data
     */
    updateChart(chartId, newData) {
        const chart = this.charts.get(chartId);
        if (!chart) return false;

        // Update labels
        if (newData.labels) {
            chart.data.labels = newData.labels;
        }

        // Update datasets
        if (newData.datasets) {
            newData.datasets.forEach((dataset, index) => {
                if (chart.data.datasets[index]) {
                    Object.assign(chart.data.datasets[index], dataset);
                }
            });
        }

        chart.update();
        return true;
    }

    /**
     * Destroy chart
     */
    destroyChart(chartId) {
        const chart = this.charts.get(chartId);
        if (chart) {
            chart.destroy();
            this.charts.delete(chartId);
            return true;
        }
        return false;
    }

    /**
     * Destroy all charts
     */
    destroyAllCharts() {
        this.charts.forEach((chart, id) => {
            chart.destroy();
        });
        this.charts.clear();
    }

    /**
     * Resize all charts
     */
    resizeCharts() {
        this.charts.forEach(chart => {
            chart.resize();
        });
    }
}

/**
 * Dashboard Statistics Module
 */
const DashboardStats = {
    chartManager: new ChartManager(),

    async loadAttendanceOverview(containerId = 'attendance-overview-chart') {
        try {
            FaceID.LoadingManager.show(`#${containerId}`, 'Đang tải biểu đồ...');
            
            const response = await FaceID.APIClient.get('/api/statistics/attendance-overview');
            
            if (response.success) {
                this.chartManager.createAttendanceOverview(containerId, response.data);
            }
        } catch (error) {
            console.error('Error loading attendance overview:', error);
            FaceID.NotificationSystem.error('Lỗi khi tải biểu đồ tổng quan');
        } finally {
            FaceID.LoadingManager.hide(`#${containerId}`);
        }
    },

    async loadDailyAttendance(containerId = 'daily-attendance-chart', days = 7) {
        try {
            FaceID.LoadingManager.show(`#${containerId}`, 'Đang tải biểu đồ...');
            
            const response = await FaceID.APIClient.get(`/api/statistics/daily-attendance?days=${days}`);
            
            if (response.success) {
                this.chartManager.createDailyAttendanceChart(containerId, response.data);
            }
        } catch (error) {
            console.error('Error loading daily attendance:', error);
            FaceID.NotificationSystem.error('Lỗi khi tải biểu đồ điểm danh hàng ngày');
        } finally {
            FaceID.LoadingManager.hide(`#${containerId}`);
        }
    },

    async loadClassComparison(containerId = 'class-comparison-chart') {
        try {
            FaceID.LoadingManager.show(`#${containerId}`, 'Đang tải biểu đồ...');
            
            const response = await FaceID.APIClient.get('/api/statistics/class-comparison');
            
            if (response.success) {
                this.chartManager.createClassComparisonChart(containerId, response.data);
            }
        } catch (error) {
            console.error('Error loading class comparison:', error);
            FaceID.NotificationSystem.error('Lỗi khi tải biểu đồ so sánh lớp học');
        } finally {
            FaceID.LoadingManager.hide(`#${containerId}`);
        }
    },

    async loadMonthlyTrend(containerId = 'monthly-trend-chart', months = 6) {
        try {
            FaceID.LoadingManager.show(`#${containerId}`, 'Đang tải biểu đồ...');
            
            const response = await FaceID.APIClient.get(`/api/statistics/monthly-trend?months=${months}`);
            
            if (response.success) {
                this.chartManager.createMonthlyTrendChart(containerId, response.data);
            }
        } catch (error) {
            console.error('Error loading monthly trend:', error);
            FaceID.NotificationSystem.error('Lỗi khi tải biểu đồ xu hướng tháng');
        } finally {
            FaceID.LoadingManager.hide(`#${containerId}`);
        }
    }
};

/**
 * Report Charts Module
 */
const ReportCharts = {
    chartManager: new ChartManager(),

    async generateAttendanceReport(params = {}) {
        try {
            FaceID.LoadingManager.show(null, 'Đang tạo báo cáo...');
            
            const queryParams = new URLSearchParams(params).toString();
            const response = await FaceID.APIClient.get(`/api/reports/attendance?${queryParams}`);
            
            if (response.success) {
                this.renderReportCharts(response.data);
                FaceID.NotificationSystem.success('Báo cáo đã được tạo thành công');
            }
        } catch (error) {
            console.error('Error generating report:', error);
            FaceID.NotificationSystem.error('Lỗi khi tạo báo cáo');
        } finally {
            FaceID.LoadingManager.hide();
        }
    },

    renderReportCharts(data) {
        // Clear existing charts
        this.chartManager.destroyAllCharts();

        // Render overview chart
        if (data.overview && document.getElementById('report-overview-chart')) {
            this.chartManager.createAttendanceOverview('report-overview-chart', data.overview);
        }

        // Render daily trend chart
        if (data.daily_trend && document.getElementById('report-daily-chart')) {
            this.chartManager.createDailyAttendanceChart('report-daily-chart', data.daily_trend);
        }

        // Render class comparison chart
        if (data.class_comparison && document.getElementById('report-class-chart')) {
            this.chartManager.createClassComparisonChart('report-class-chart', data.class_comparison);
        }

        // Render time slot chart
        if (data.time_slots && document.getElementById('report-timeslot-chart')) {
            this.chartManager.createTimeSlotChart('report-timeslot-chart', data.time_slots);
        }
    },

    exportChart(chartId, filename) {
        const chart = this.chartManager.charts.get(chartId);
        if (!chart) {
            FaceID.NotificationSystem.error('Không tìm thấy biểu đồ để xuất');
            return;
        }

        const url = chart.toBase64Image();
        FaceID.Utils.downloadFile(url, filename || 'chart.png');
        FaceID.NotificationSystem.success('Đã xuất biểu đồ thành công');
    }
};

// Auto-initialize charts on page load
FaceID.DOMUtils.ready(() => {
    // Initialize dashboard charts
    if (document.body.classList.contains('dashboard-page')) {
        DashboardStats.loadAttendanceOverview();
        DashboardStats.loadDailyAttendance();
        DashboardStats.loadClassComparison();
        DashboardStats.loadMonthlyTrend();
    }

    // Initialize report charts
    if (document.body.classList.contains('report-page')) {
        // Charts will be loaded when user generates a report
        console.log('Report page ready for chart generation');
    }

    // Handle window resize
    window.addEventListener('resize', FaceID.Utils.debounce(() => {
        DashboardStats.chartManager.resizeCharts();
        ReportCharts.chartManager.resizeCharts();
    }, 250));

    // Setup chart export buttons
    document.querySelectorAll('[data-export-chart]').forEach(button => {
        button.addEventListener('click', function() {
            const chartId = this.getAttribute('data-export-chart');
            const filename = this.getAttribute('data-filename') || 'chart.png';
            ReportCharts.exportChart(chartId, filename);
        });
    });
});

// Export for global use
window.FaceID = window.FaceID || {};
window.FaceID.Charts = {
    ChartManager,
    DashboardStats,
    ReportCharts
};
