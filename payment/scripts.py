create_script = """
CREATE TABLE IF NOT EXISTS users
(
    user_id uuid DEFAULT gen_random_uuid(),
    credit double precision NOT NULL DEFAULT 0,
    CONSTRAINT Users_pkey PRIMARY KEY (user_id),
    CONSTRAINT credit_positive CHECK ( credit >= 0 )
);

CREATE TABLE IF NOT EXISTS payments
(
    user_id uuid NOT NULL,
    order_id uuid NOT NULL,
    amount double precision NOT NULL,
    CONSTRAINT Payments_pkey PRIMARY KEY (user_id, order_id),
    CONSTRAINT Users_fk FOREIGN KEY (user_id)
        REFERENCES Users (user_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);
"""

user_insert_script = "INSERT INTO Users DEFAULT VALUES RETURNING user_id;"

user_find_script = "SELECT * FROM Users WHERE user_id = %s;"

user_add_credit_script = "UPDATE Users SET credit = credit + %s WHERE user_id = %s RETURNING credit;"

user_remove_credit_script = "UPDATE Users SET credit = credit - %s WHERE user_id = %s RETURNING credit;"

payment_insert_script = "INSERT INTO Payments VALUES (%s, %s, %s) RETURNING *;"

payment_get_status_script = "SELECT * FROM Payments WHERE user_id = %s AND order_id = %s;"

check_user_script = "SELECT COUNT(1) FROM Users WHERE user_id = %s;"
