create_table_script = """
CREATE TABLE IF NOT EXISTS Stock
(
    item_id uuid DEFAULT gen_random_uuid(),
    price double precision NOT NULL DEFAULT 0,
    stock INT NOT NULL DEFAULT 0,
    CONSTRAINT Items_pkey PRIMARY KEY (item_id),
    CONSTRAINT Price_positive CHECK ( price >= 0 ),
    CONSTRAINT Stock_positive CHECK ( stock >= 0 )
);"""

insert_item_script = "INSERT INTO Stock (item_id, price, stock) VALUES (DEFAULT, %s, DEFAULT) RETURNING item_id;"

find_item_script = "SELECT * FROM Stock WHERE item_id = %s;"

add_item_stock_script = "UPDATE Stock SET stock = stock + %s WHERE item_id = %s RETURNING stock;"

remove_item_stock_script = "UPDATE Stock SET stock = stock - %s WHERE item_id = %s RETURNING stock;"

calculate_cost_script = "SELECT item_id, price, stock FROM Stock WHERE item_id IN %s;"
