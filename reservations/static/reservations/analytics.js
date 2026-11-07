async function loadAnalytics() {
    const errorBlock = document.getElementById("analytics-error");

    try {
        const response = await fetch("/api/equipment-statistics/", {
            credentials: "same-origin"
        });

        if (!response.ok) {
            throw new Error("Не удалось загрузить статистику.");
        }

        const data = await response.json();

        document.getElementById("equipment-types").textContent =
            data.equipment_types;

        document.getElementById("total-units").textContent =
            data.total_units;

        document.getElementById("available-units").textContent =
            data.available_units;

        document.getElementById("occupied-units").textContent =
            data.occupied_units;

        const statuses = [
            {name: "Созданы", count: data.created_count},
            {name: "Подтверждены", count: data.confirmed_count},
            {name: "Завершены", count: data.completed_count}
        ];

        const chart = document.getElementById("status-chart");
        chart.replaceChildren();

        const maximum = Math.max(
            ...statuses.map(item => item.count),
            1
        );

        statuses.forEach(item => {
            const label = document.createElement("p");
            label.textContent = `${item.name}: ${item.count}`;

            const progress = document.createElement("div");
            progress.className = "progress mb-3";

            const bar = document.createElement("div");
            bar.className = "progress-bar";
            bar.style.width = `${item.count / maximum * 100}%`;

            progress.appendChild(bar);
            chart.append(label, progress);
        });

        const popular = document.getElementById("popular-equipment");
        popular.replaceChildren();

        if (data.popular_equipment.length === 0) {
            popular.textContent = "Пока нет данных о бронированиях.";
        } else {
            data.popular_equipment.forEach((item, index) => {
                const row = document.createElement("p");

                row.textContent =
                    `${index + 1}. ${item.name} — ${item.count} бронирований`;

                popular.appendChild(row);
            });
        }

    } catch (error) {
        errorBlock.textContent = error.message;
    }
}

loadAnalytics();
