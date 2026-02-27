CREATE TABLE IF NOT EXISTS cultes_ejp (
    id                  SERIAL PRIMARY KEY,
    date_culte          DATE NOT NULL UNIQUE,
    nb_total_site       INT NOT NULL,
    nb_total_culte      INT NOT NULL,
    nb_hommes           INT NOT NULL,
    nb_femmes           INT NOT NULL,
    nb_appels_salut     INT NOT NULL,
    nb_nouveaux         INT NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prieres_ejp (
    id          SERIAL PRIMARY KEY,
    date_priere DATE NOT NULL,
    mode        VARCHAR(20) NOT NULL CHECK (mode IN ('PRESENTIEL', 'ZOOM')),
    nb_total    INT NOT NULL,
    nb_hommes   INT NOT NULL,
    nb_femmes   INT NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_priere_date_mode UNIQUE (date_priere, mode)
);
