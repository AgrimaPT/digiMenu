// Establish WebSocket connection
const socket = new WebSocket('ws://127.0.0.1:8000/ws/orders/');
const orderSound = new Audio('/static/sounds/order-placed.mp3');
orderSound.load();

// Handle incoming WebSocket messages
socket.onmessage = function (event) {
    const data = JSON.parse(event.data);

    // Update table boxes dynamically
    if (data.order) {
        const tableBoxElement = document.getElementById(`table-box-${data.order.table}`);
        if (tableBoxElement) {
            tableBoxElement.style.backgroundColor = data.order.has_pending_orders ? 'lightcoral' : 'lightgray';
        }

        // Play notification sound
        try {
            orderSound.play();
        } catch (error) {
            console.error("Error playing sound:", error);
        }
    }

    // Update pending orders dynamically on the pending orders page
    const pendingOrdersTable = document.getElementById('pending-orders-table');
    if (pendingOrdersTable && data.order.status === 'Pending') {
        const order = data.order;

        // Check if the order already exists in the table
        if (!document.getElementById(`order-${order.id}`)) {
            const row = document.createElement('tr');
            row.id = `order-${order.id}`;
            row.innerHTML = `
                <td>${order.id}</td>
                <td>${order.customer_name}</td>
                <td>${order.total}</td>
                <td>
                    <ul>
                        ${order.items.map(item => `
                            <li>${item.item_name} (x${item.quantity}) - ${item.price}</li>
                        `).join('')}
                    </ul>
                </td>
                <td><button onclick="markAsCompleted('${order.id}')">Mark as Completed</button></td>
            `;
            pendingOrdersTable.appendChild(row);
        }
    }
};

socket.onerror = function (error) {
    console.error("WebSocket error:", error);
};

socket.onclose = function (event) {
    console.warn("WebSocket closed:", event);
};
