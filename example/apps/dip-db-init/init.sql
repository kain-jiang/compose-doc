CREATE DATABASE IF NOT EXISTS `{{APP_DATABASE}}`;

CREATE USER IF NOT EXISTS '{{APP_USER}}'@'%' IDENTIFIED BY '{{APP_PASSWORD}}';
ALTER USER '{{APP_USER}}'@'%' IDENTIFIED BY '{{APP_PASSWORD}}';
GRANT ALL PRIVILEGES ON `{{APP_DATABASE}}`.* TO '{{APP_USER}}'@'%';
FLUSH PRIVILEGES;

USE `{{APP_DATABASE}}`;

CREATE TABLE IF NOT EXISTS demo_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(128) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO demo_messages (title, content)
SELECT 'welcome', 'dip-db-init inserted the first demo record'
WHERE NOT EXISTS (
    SELECT 1 FROM demo_messages WHERE title = 'welcome'
);

INSERT INTO demo_messages (title, content)
SELECT 'status', 'dip-api can now read MySQL data through /api/dip-api/messages'
WHERE NOT EXISTS (
    SELECT 1 FROM demo_messages WHERE title = 'status'
);
