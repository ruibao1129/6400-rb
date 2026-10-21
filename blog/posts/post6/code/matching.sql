
CREATE TABLE matches AS
SELECT c.child_id, c.mother_id, c.birth_year,
       c.sex, m.birth_year AS mother_birth_year
FROM children AS c
JOIN mothers AS m ON c.mother_id = m.mother_id;


SELECT child_id, AVG(real_income) AS child_avg,
       COUNT(DISTINCT income_year) AS child_years
FROM child_income
WHERE age BETWEEN 30 AND 39
GROUP BY child_id
HAVING COUNT(DISTINCT income_year) >= 3
;
