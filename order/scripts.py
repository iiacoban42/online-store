create_script = """
CREATE TABLE IF NOT EXISTS public.\"Users\"
(
    user_id SERIAL PRIMARY KEY,
    credit double precision NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS public.\"Orders\"
(
    order_id SERIAL PRIMARY KEY,
    paid boolean NOT NULL,
    items int[] NOT NULL,
    user_id int NOT NULL,
    total_cost double precision NOT NULL,

    CONSTRAINT Users_fk FOREIGN KEY (user_id)
        REFERENCES public.\"Users\" (user_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);
"""

user_insert_script = "INSERT INTO public.\"Users\" DEFAULT VALUES RETURNING user_id;"