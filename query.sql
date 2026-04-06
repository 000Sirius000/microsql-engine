SELECT name, salary
FROM users.csv
WHERE salary > 2000 AND role = 'user'
ORDER BY salary DESC
