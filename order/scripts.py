create_orders_table = """
CREATE TABLE IF NOT EXISTS orders
(
    order_id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    paid boolean NOT NULL,
    items uuid[] NOT NULL,
    user_id uuid NOT NULL,
    total_cost double precision NOT NULL
);
"""

create_order_script = """
INSERT INTO orders (order_id, paid, items, user_id, total_cost)
VALUES (%s, FALSE, ARRAY[]::uuid[], %s, 0) RETURNING *;
"""

remove_order_script = "DELETE FROM orders WHERE order_id = %s RETURNING *;"

find_order_script = "SELECT * FROM orders WHERE order_id = %s;"

add_item_script = "UPDATE orders SET items = array_append(items, %s) WHERE order_id = %s AND paid = FALSE RETURNING order_id;"

remove_item_script = "UPDATE orders SET items = array_remove(items, %s) WHERE order_id = %s AND paid = FALSE RETURNING order_id;"

update_cost_script = "UPDATE orders SET total_cost = %s WHERE order_id = %s RETURNING *;"

update_items_script = "UPDATE orders SET items = %s WHERE order_id = %s RETURNING *;"

update_payment_status_script = "UPDATE orders SET paid = %s WHERE order_id = %s RETURNING *;"