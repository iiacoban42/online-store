create_users_table = """
CREATE TABLE IF NOT EXISTS public.\"Users\"
(
    user_id SERIAL PRIMARY KEY,
    credit double precision NOT NULL DEFAULT 0
);
"""

create_orders_table = """
CREATE TABLE IF NOT EXISTS public.\"Orders\"
(
    order_id SERIAL PRIMARY KEY,
    paid boolean NOT NULL,
    items int[] NOT NULL,
    user_id int NOT NULL,
    total_cost double precision NOT NULL,
    CONSTRAINT users_fk FOREIGN KEY(user_id)
        REFERENCES public.\"Users\"(user_id)
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);
"""

user_insert_script = "INSERT INTO public.\"Users\" DEFAULT VALUES RETURNING user_id;"

create_order_script = """
INSERT INTO public.\"Orders\" (order_id, paid, items, user_id, total_cost)
VALUES (DEFAULT, FALSE, ARRAY[]::int[], %s, 0) RETURNING order_id;
"""

remove_order_script = "DELETE FROM public.\"Orders\" WHERE order_id = %s;"

find_order_script = "SELECT * FROM public.\"Orders\" WHERE order_id = %s;"

add_item_script = "UPDATE public.\"Orders\" SET items = array_append(items, %s) WHERE order_id = %s;"

remove_item_script = "UPDATE public.\"Orders\" SET items = array_remove(items, %s) WHERE order_id = %s;"