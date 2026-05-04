SELECT name, salary
FROM users.csv
WHERE (salary > 2000 AND role = 'user') OR (salary > 5000)
ORDER BY salary DESC
