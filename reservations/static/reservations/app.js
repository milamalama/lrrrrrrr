const csrfToken = document.querySelector(
    "[name=csrfmiddlewaretoken]"
).value;

let selectedReservationId = null;
let equipmentRequestNumber = 0;


async function api(url, method = "GET", data = null) {
    const options = {
        method: method,
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        }
    };

    if (data !== null) {
        options.body = JSON.stringify(data);
    }

    let response;

    try {
        response = await fetch(url, options);
    } catch (error) {
        throw new Error("Не удалось подключиться к серверу.");
    }

    const result = response.status === 204
        ? null
        : await response.json().catch(() => null);

    if (!response.ok) {
        const errorText = result
            ? JSON.stringify(result)
            : "Ошибка сервера";

        throw new Error(errorText);
    }

    return result;
}


function message(text, error = false) {
    const block = document.getElementById("message");

    block.className = error
        ? "alert alert-danger"
        : "alert alert-success";

    block.textContent = text;
}


function addButton(container, text, className, handler) {
    const button = document.createElement("button");

    button.type = "button";
    button.className = className;
    button.textContent = text;

    button.addEventListener("click", async () => {
        button.disabled = true;

        try {
            await handler();
        } finally {
            button.disabled = false;
        }
    });

    container.appendChild(button);
}


async function loadFilters() {
    const equipment = await api("/api/equipment/");

    const categories = [
        ...new Set(equipment.map(item => item.category))
    ].sort();

    const categorySelect = document.getElementById("category-filter");
    const reservationFilter = document.getElementById("equipment-filter");

    categorySelect.replaceChildren();
    reservationFilter.replaceChildren();

    categorySelect.add(new Option("Все категории", ""));
    reservationFilter.add(new Option("Всё оборудование", ""));

    categories.forEach(category => {
        categorySelect.add(new Option(category, category));
    });

    equipment.forEach(item => {
        reservationFilter.add(new Option(item.name, item.id));
    });
}


async function loadEquipment() {
    const search = document.getElementById("equipment-search")
        .value.trim();

    const category = document.getElementById("category-filter").value;

    const select = document.getElementById("equipment");
    const createButton = document.getElementById(
        "create-reservation-btn"
    );

    const previousValue = select.value;

    const requestNumber = ++equipmentRequestNumber;

    createButton.disabled = true;
    select.disabled = true;

    const params = new URLSearchParams();

    if (search) {
        params.set("search", search);
    }

    if (category) {
        params.set("category", category);
    }

    const url = "/api/equipment/?" + params.toString();

    let equipment;

    try {
        equipment = await api(url);
    } catch (error) {
        if (requestNumber === equipmentRequestNumber) {
            select.replaceChildren();
            select.add(new Option("Ошибка загрузки", ""));
            message(error.message, true);
        }
        return;
    }

    if (requestNumber !== equipmentRequestNumber) {
        return;
    }

    equipment = equipment.filter(item => {
        const matchesName = item.name
            .toLocaleLowerCase("ru")
            .includes(search.toLocaleLowerCase("ru"));

        const matchesCategory =
            !category || item.category === category;

        return matchesName && matchesCategory;
    });

    select.replaceChildren();

    if (equipment.length === 0) {
        select.add(new Option("Оборудование не найдено", ""));
        select.disabled = true;
        createButton.disabled = true;
        return;
    }

    equipment.forEach(item => {
        select.add(new Option(
            `${item.name} — доступно: ${item.available_quantity}`,
            item.id
        ));
    });

    const stillExists = equipment.some(
        item => String(item.id) === previousValue
    );

    if (stillExists) {
        select.value = previousValue;
    } else {
        select.selectedIndex = 0;
    }

    select.disabled = false;
    createButton.disabled = false;
}


async function loadReservations() {
    const status = document.getElementById("status-filter").value;
    const equipment = document.getElementById("equipment-filter").value;

    const params = new URLSearchParams();

    if (status) {
        params.set("status", status);
    }

    if (equipment) {
        params.set("equipment", equipment);
    }

    const reservations = await api(
        "/api/reservations/?" + params.toString()
    );

    const list = document.getElementById("reservation-list");
    list.replaceChildren();

    if (reservations.length === 0) {
        list.textContent = "Бронирования не найдены.";
        return;
    }

    const statusNames = {
        created: "Создана",
        confirmed: "Подтверждена",
        completed: "Завершена"
    };

    reservations.forEach(reservation => {
        const card = document.createElement("div");
        card.className = "border rounded p-3 mb-3";

        const title = document.createElement("h4");
        title.textContent =
            `${reservation.equipment_name} — ${reservation.quantity} шт.`;

        const statusText = document.createElement("p");
        statusText.textContent =
            "Статус: " + statusNames[reservation.status];

        const buttons = document.createElement("div");
        buttons.className = "d-flex gap-2 flex-wrap";

        if (reservation.status === "created") {
            addButton(
                buttons, "Подтвердить", "btn btn-primary",
                () => runAction(reservation.id, "confirm")
            );

            addButton(
                buttons, "Изменить", "btn btn-outline-primary",
                () => editReservation(reservation)
            );
        }

        if (reservation.status === "confirmed") {
            addButton(
                buttons, "Завершить", "btn btn-success",
                () => runAction(reservation.id, "complete")
            );
        }

        addButton(
            buttons, "История", "btn btn-secondary",
            () => loadHistory(reservation.id)
        );

        if (reservation.status !== "confirmed") {
            addButton(
                buttons, "Удалить", "btn btn-danger",
                () => deleteReservation(reservation.id)
            );
        }

        card.append(title, statusText, buttons);
        list.appendChild(card);
    });
}


async function refreshData() {
    await loadEquipment();
    await loadReservations();

    if (selectedReservationId !== null) {
        await loadHistory(selectedReservationId);
    }
}


async function runAction(id, action) {
    try {
        const result = await api(
            `/api/reservations/${id}/${action}/`,
            "POST"
        );

        message(result.message);
        await refreshData();
    } catch (error) {
        message(error.message, true);
    }
}


async function editReservation(reservation) {
    const value = prompt(
        "Введите новое количество:",
        reservation.quantity
    );

    if (value === null) return;

    try {
        await api(
            `/api/reservations/${reservation.id}/`,
            "PATCH",
            {quantity: Number(value)}
        );

        message("Бронирование изменено.");
        await refreshData();
    } catch (error) {
        message(error.message, true);
    }
}


async function deleteReservation(id) {
    if (!confirm("Удалить бронирование?")) return;

    try {
        await api(`/api/reservations/${id}/`, "DELETE");

        if (selectedReservationId === id) {
            selectedReservationId = null;
            document.getElementById("history").textContent =
                "Бронирование удалено. История сохранена в базе.";
        }

        message("Бронирование удалено.");
        await refreshData();
    } catch (error) {
        message(error.message, true);
    }
}


async function loadHistory(id) {
    try {
        const events = await api(
            `/api/reservations/${id}/history/`
        );

        selectedReservationId = id;

        const history = document.getElementById("history");
        history.replaceChildren();

        events.forEach(event => {
            const row = document.createElement("p");

            row.textContent =
                `${event.action} — ${event.actor_name || "Система"} — ` +
                new Date(event.created_at).toLocaleString("ru-RU");

            history.appendChild(row);
        });

        if (events.length === 0) {
            history.textContent = "История пока пуста.";
        }
    } catch (error) {
        message(error.message, true);
    }
}


document.getElementById("reservation-form")
    .addEventListener("submit", async event => {
        event.preventDefault();

        const equipmentSelect = document.getElementById("equipment");
        const button = document.getElementById("create-reservation-btn");

        if (equipmentSelect.disabled || !equipmentSelect.value) {
            message("Сначала выберите оборудование.", true);
            return;
        }

        const equipment = Number(equipmentSelect.value);
        const quantity = Number(document.getElementById("quantity").value);

        if (!Number.isInteger(quantity) || quantity < 1) {
            message("Введите корректное количество.", true);
            return;
        }

        button.disabled = true;

        try {
            await api("/api/reservations/", "POST", {
                equipment: equipment,
                quantity: quantity
            });

            message("Бронирование создано!");
            document.getElementById("quantity").value = 1;
            await refreshData();
        } catch (error) {
            message(error.message, true);
        } finally {
            button.disabled = false;
        }
    });


document.getElementById("equipment-search")
    .addEventListener("input", loadEquipment);


document.getElementById("category-filter")
    .addEventListener("change", loadEquipment);


document.getElementById("equipment-search")
    .addEventListener("keydown", event => {
        if (event.key === "Enter") {
            event.preventDefault();
        }
    });


document.getElementById("status-filter")
    .addEventListener("change", loadReservations);

document.getElementById("equipment-filter")
    .addEventListener("change", loadReservations);


async function initialize() {
    try {
        await loadFilters();
        await refreshData();
    } catch (error) {
        message(error.message, true);
    }
}

initialize();
