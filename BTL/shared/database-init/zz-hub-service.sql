-- Additive only; run on existing hunre_ecommerce. No shared data reset.
CREATE TABLE IF NOT EXISTS hub_access_tokens (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 user_id BIGINT UNSIGNED NOT NULL,
 token_hash CHAR(64) NOT NULL UNIQUE,
 expires_at TIMESTAMP NOT NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 INDEX hub_token_user (user_id),
 FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS hub_events (
 id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
 order_id BIGINT UNSIGNED NOT NULL,
 locker_id INT UNSIGNED NOT NULL,
 staff_id BIGINT UNSIGNED NOT NULL,
 action VARCHAR(30) NOT NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 INDEX hub_event_order (order_id),
 FOREIGN KEY (order_id) REFERENCES escrow_orders(id),
 FOREIGN KEY (locker_id) REFERENCES lockers(id),
 FOREIGN KEY (staff_id) REFERENCES users(id)
) ENGINE=InnoDB;
