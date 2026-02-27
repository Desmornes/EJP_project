INSERT INTO cultes_ejp (date_culte, nb_total_site, nb_total_culte, nb_hommes, nb_femmes, nb_appels_salut, nb_nouveaux)
VALUES
('2026-01-04', 67, 53, 26, 27, 0, 3),
('2026-01-11', 78, 54, 22, 32, 0, 3)
ON CONFLICT (date_culte) DO NOTHING;

INSERT INTO prieres_ejp (date_priere, mode, nb_total, nb_hommes, nb_femmes)
VALUES
('2026-02-13', 'PRESENTIEL', 17, 10, 7)
ON CONFLICT (date_priere, mode) DO NOTHING;
