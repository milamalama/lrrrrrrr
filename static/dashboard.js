(() => {
    'use strict';

    const root = document.getElementById('dashboard-root');

    if (!root) {
        return;
    }

    const $ = id => document.getElementById(id);
    const section = root.dataset.section;

    const colors = [
        '#e9a8c4',
        '#cdefd8',
        '#d5eefa',
        '#dccaf1',
        '#f4d7b4',
        '#c5e9e3',
        '#f5c5d9',
        '#cbd7ff',
        '#e8dfc0',
        '#bcd4c6',
        '#d9c4ee',
        '#f6d2cb'
    ];

    let charts = [];
    let current = null;

    function short(text) {
        const value = String(text ?? '');

        return value.length > 29
            ? value.slice(0, 26) + '…'
            : value;
    }

    function status(message) {
        const element = $('dashboard-status');

        if (element) {
            element.textContent = message;
        }
    }

    function setText(id, value) {
        const element = $(id);

        if (element) {
            element.textContent = value ?? '—';
        }
    }

    function draw(
        id,
        type,
        labels,
        datasets,
        horizontal = false
    ) {
        const canvas = $(id);

        if (!canvas) {
            return;
        }

        if (!window.Chart) {
            status('Ошибка: библиотека Chart.js не загружена');
            return;
        }

        const chart = new Chart(canvas, {
            type: type,

            data: {
                labels: labels,
                datasets: datasets
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

                indexAxis: horizontal ? 'y' : 'x',

                plugins: {
                    legend: {
                        display:
                            datasets.length > 1 ||
                            type === 'doughnut'
                    },

                    tooltip: {
                        callbacks: {
                            title(items) {
                                if (!items.length) {
                                    return '';
                                }

                                return labels[
                                    items[0].dataIndex
                                ] || '';
                            }
                        }
                    }
                },

                scales: type === 'doughnut'
                    ? {}
                    : {
                        x: {
                            ticks: {
                                autoSkip: false,
                                maxRotation: 65,
                                minRotation: 0
                            }
                        },

                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
            }
        });

        charts.push(chart);
    }

    function renderCharts(data) {

        charts.forEach(chart => chart.destroy());
        charts = [];

        const departments = data.departments || [];
        const groupsData = data.groups || [];

        const labels = departments.map(
            department => short(department.name)
        );

        const courses = departments.map(
            department => department.courses_count
        );

        const groups = departments.map(
            department => department.groups_count
        );

        const students = departments.map(
            department => department.students_count
        );

        if (section === 'overview') {

            draw(
                'chart-one',
                'bar',
                labels,
                [{
                    label: 'Курсы',
                    data: courses,
                    backgroundColor: '#e9a8c4'
                }],
                true
            );

            draw(
                'chart-two',
                'bar',
                labels,
                [{
                    label: 'Группы',
                    data: groups,
                    backgroundColor: '#cdefd8'
                }],
                true
            );
        }

        else if (section === 'departments') {

            draw(
                'chart-one',
                'bar',
                labels,
                [
                    {
                        label: 'Курсы',
                        data: courses,
                        backgroundColor: '#e9a8c4'
                    },
                    {
                        label: 'Группы',
                        data: groups,
                        backgroundColor: '#cdefd8'
                    }
                ],
                true
            );

            draw(
                'chart-two',
                'doughnut',
                labels,
                [{
                    label: 'Группы',
                    data: groups,
                    backgroundColor: colors
                }]
            );
        }

        else if (section === 'groups') {

            draw(
                'chart-one',
                'bar',
                groupsData.map(group => group.name),
                [{
                    label: 'Студенты',
                    data: groupsData.map(
                        group => group.students_count
                    ),
                    backgroundColor: '#d5eefa'
                }],
                true
            );

            draw(
                'chart-two',
                'bar',
                labels,
                [{
                    label: 'Группы',
                    data: groups,
                    backgroundColor: '#cdefd8'
                }],
                true
            );
        }

        draw(
            'chart-students',
            'bar',
            labels,
            [{
                label: 'Студенты',
                data: students,
                backgroundColor: '#e9a8c4'
            }],
            true
        );
    }

    function createCell(value) {
        const cell = document.createElement('td');

        cell.textContent = String(value ?? '');

        return cell;
    }

    function renderTable(data) {

        const head = $('dashboard-table-head');
        const body = $('dashboard-table-body');

        if (!head || !body) {
            return;
        }

        head.replaceChildren();
        body.replaceChildren();

        const isGroups = section === 'groups';
        const isCourses = section === 'overview';

        let columns = [];
        let rows = [];

        if (isGroups) {

            columns = [
                'Группа',
                'Факультет',
                'Студентов'
            ];

            rows = (data.groups || []).map(group => [
                group.name,
                group.department__name,
                group.students_count
            ]);
        }

        else if (isCourses) {

            columns = [
                'Курс',
                'Факультет'
            ];

            rows = (data.courses || []).map(course => [
                course.title,
                course.department__name
            ]);
        }

        else {

            columns = [
                'Факультет',
                'Курсов',
                'Групп',
                'Студентов'
            ];

            rows = (data.departments || []).map(
                department => [
                    department.name,
                    department.courses_count,
                    department.groups_count,
                    department.students_count
                ]
            );
        }

        const headerRow = document.createElement('tr');

        columns.forEach(column => {
            const th = document.createElement('th');

            th.textContent = column;
            headerRow.appendChild(th);
        });

        head.appendChild(headerRow);

        const searchInput = $('dashboard-search');

        const search = searchInput
            ? searchInput.value.toLocaleLowerCase('ru')
            : '';

        const filteredRows = rows.filter(row =>
            row.some(value =>
                String(value ?? '')
                    .toLocaleLowerCase('ru')
                    .includes(search)
            )
        );

        if (filteredRows.length === 0) {

            const emptyRow = document.createElement('tr');
            const emptyCell = createCell(
                'Нет данных для выбранного фильтра'
            );

            emptyCell.colSpan = columns.length;

            emptyRow.appendChild(emptyCell);
            body.appendChild(emptyRow);

            return;
        }

        filteredRows.forEach(row => {

            const tableRow = document.createElement('tr');

            row.forEach(value => {
                tableRow.appendChild(createCell(value));
            });

            body.appendChild(tableRow);
        });
    }

    function renderSummary(data) {

        const summary = data.summary || {};

        Object.entries(summary).forEach(([key, value]) => {
            setText('stat-' + key, value);
        });
    }

    function renderExtra(data) {

        const extra = data.extra || {};

        setText(
            'stat-average',
            extra.average_group_size ?? '—'
        );

        const largestGroup = extra.largest_group;

        setText(
            'stat-largest-group',
            largestGroup
                ? largestGroup.name
                : 'Нет данных'
        );

        setText(
            'stat-largest-group-count',
            largestGroup
                ? 'Студентов: ' + largestGroup.students
                : ''
        );

        const topDepartment = extra.top_department;

        setText(
            'stat-top-department',
            topDepartment
                ? topDepartment.name
                : 'Нет данных'
        );

        setText(
            'stat-top-department-count',
            topDepartment
                ? 'Студентов: ' + topDepartment.students
                : ''
        );
    }

    async function load() {

        status('Загрузка данных…');

        const params = new URLSearchParams();

        const filter = $('department-filter');

        const department = filter
            ? filter.value
            : '';

        if (department) {
            params.set('department', department);
        }

        try {

            const response = await fetch(
                root.dataset.api + '?' + params.toString(),
                {
                    cache: 'no-store',
                    credentials: 'same-origin'
                }
            );

            if (!response.ok) {
                throw new Error(
                    'HTTP ' + response.status
                );
            }

            const data = await response.json();

            current = data;

            renderSummary(data);

            renderExtra(data);

            renderCharts(data);

            renderTable(data);

            status(
                'Данные обновлены: ' +
                new Date().toLocaleTimeString('ru-RU')
            );

        } catch (error) {

            console.error(
                'Ошибка загрузки аналитики:',
                error
            );

            status(
                'Ошибка загрузки: ' + error.message
            );
        }
    }

    const departmentFilter = $('department-filter');

    if (departmentFilter) {
        departmentFilter.addEventListener(
            'change',
            load
        );
    }

    const refreshButton = $('refresh-dashboard');

    if (refreshButton) {
        refreshButton.addEventListener(
            'click',
            load
        );
    }

    const searchInput = $('dashboard-search');

    if (searchInput) {
        searchInput.addEventListener(
            'input',
            () => {
                if (current) {
                    renderTable(current);
                }
            }
        );
    }

    load();

})();

