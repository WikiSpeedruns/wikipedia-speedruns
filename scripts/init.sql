CREATE USER 'user'@'%';
GRANT ALL PRIVILEGES ON wikipedia_speedruns.* TO 'user'@'%';
FLUSH PRIVILEGES;