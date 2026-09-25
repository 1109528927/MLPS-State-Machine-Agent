-- 首次启动 MySQL 时自动执行（仅空数据卷生效）
CREATE DATABASE IF NOT EXISTS mini_agent_2 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mini_agent_2;

CREATE TABLE IF NOT EXISTS `user` (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  employee_no VARCHAR(50) NOT NULL UNIQUE,
  role VARCHAR(20) NOT NULL DEFAULT 'inspector',
  create_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_token (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  token VARCHAR(255) NOT NULL UNIQUE,
  expires_at DATETIME NOT NULL,
  create_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES `user`(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS project (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  remark VARCHAR(255) NULL,
  create_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS project_member (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  project_id INT NOT NULL,
  create_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_user_project (user_id, project_id),
  FOREIGN KEY (user_id) REFERENCES `user`(id),
  FOREIGN KEY (project_id) REFERENCES project(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS gap_item (
  id INT AUTO_INCREMENT PRIMARY KEY,
  project_id INT NOT NULL,
  title VARCHAR(200) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT '待整改',
  category VARCHAR(50) NULL,
  risk_level VARCHAR(20) NULL,
  reason TEXT NULL,
  requirement TEXT NULL,
  create_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES project(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS gap_action_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  gap_id INT NOT NULL,
  actor_id INT NOT NULL,
  action VARCHAR(20) NOT NULL,
  from_status VARCHAR(20) NOT NULL,
  to_status VARCHAR(20) NOT NULL,
  comment TEXT NULL,
  create_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (gap_id) REFERENCES gap_item(id),
  FOREIGN KEY (actor_id) REFERENCES `user`(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS chat_records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_input TEXT NOT NULL,
  agent_output TEXT NOT NULL,
  create_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 种子账号：manager / 123456（bcrypt）
INSERT INTO `user` (username, password, employee_no, role)
VALUES (
  'manager',
  '$2b$12$ExubSP/eP5QzG2tyXcDfQe5kCvw54bl3Eulb8J/n3jXJROhkIq/yG',
  'E0001',
  'manager'
)
ON DUPLICATE KEY UPDATE username = username;

INSERT INTO `user` (username, password, employee_no, role)
VALUES (
  'inspector',
  '$2b$12$ExubSP/eP5QzG2tyXcDfQe5kCvw54bl3Eulb8J/n3jXJROhkIq/yG',
  'E0002',
  'inspector'
)
ON DUPLICATE KEY UPDATE username = username;

INSERT INTO project (name, remark) VALUES
  ('a业务系统等保测评', '演示被测系统'),
  ('b业务系统等保测评', '演示第二个被测系统')
ON DUPLICATE KEY UPDATE name = name;

INSERT INTO project_member (user_id, project_id)
SELECT u.id, p.id FROM `user` u, project p
WHERE u.username = 'inspector' AND p.name = 'a业务系统等保测评'
ON DUPLICATE KEY UPDATE user_id = user_id;
