create_orders_table = """
CREATE TABLE IF NOT EXISTS public.\"Orders\"
(
    order_id SERIAL PRIMARY KEY,
    paid boolean NOT NULL,
    items int[] NOT NULL,
    user_id int NOT NULL,
    total_cost double precision NOT NULL
);
"""

create_order_script = """
INSERT INTO public.\"Orders\" (order_id, paid, items, user_id, total_cost)
VALUES (DEFAULT, FALSE, ARRAY[]::int[], %s, 0) RETURNING order_id;
"""

remove_order_script = "DELETE FROM public.\"Orders\" WHERE order_id = %s;"

find_order_script = "SELECT * FROM public.\"Orders\" WHERE order_id = %s;"

add_item_script = "UPDATE public.\"Orders\" SET items = array_append(items, %s) WHERE order_id = %s AND paid = FALSE RETURNING order_id;"

remove_item_script = "UPDATE public.\"Orders\" SET items = array_remove(items, %s) WHERE order_id = %s AND paid = FALSE RETURNING order_id;"

update_cost_script = "UPDATE public.\"Orders\" SET total_cost = %s WHERE order_id = %s;"

update_items_script = "UPDATE public.\"Orders\" SET items = %s WHERE order_id = %s;"

update_payment_status_script = "UPDATE public.\"Orders\" SET paid = %s WHERE order_id = %s;"