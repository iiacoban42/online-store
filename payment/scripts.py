create_script = """
CREATE TABLE IF NOT EXISTS public.\"Users\"
(
    user_id SERIAL,
    credit double precision NOT NULL DEFAULT 0,
    CONSTRAINT Users_pkey PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS public.\"Payments\"
(
    user_id int NOT NULL,
    order_id int NOT NULL,
    amount double precision NOT NULL,
    payed boolean NOT NULL,
    CONSTRAINT Payments_pkey PRIMARY KEY (user_id, order_id),
    CONSTRAINT Users_fk FOREIGN KEY (user_id)
        REFERENCES public.\"Users\" (user_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);
"""

user_insert_script = "INSERT INTO public.\"Users\" DEFAULT VALUES RETURNING user_id;"