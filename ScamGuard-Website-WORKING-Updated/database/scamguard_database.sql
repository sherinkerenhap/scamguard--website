-- ScamGuard MySQL Database
-- Run this file in MySQL Workbench / MySQL command line.

CREATE DATABASE IF NOT EXISTS scamguard
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE scamguard;

CREATE TABLE IF NOT EXISTS scam_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    label VARCHAR(20) NOT NULL,
    source VARCHAR(100) DEFAULT 'ScamGuard',
    category VARCHAR(50) DEFAULT 'SMS',
    risk_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scan_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message TEXT NOT NULL,
    result VARCHAR(30) NOT NULL,
    risk_score INT NOT NULL,
    risk_level VARCHAR(30) NOT NULL,
    detected_indicators TEXT,
    recommendation TEXT,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample records for testing.
INSERT INTO scam_messages (message, label, source, category, risk_score) VALUES
('Congratulations! You won a cash prize. Click this link now.', 'SPAM', 'ScamGuard Sample', 'SMS', 95),
('URGENT! Your bank account will be blocked. Verify immediately.', 'SPAM', 'ScamGuard Sample', 'SMS', 92),
('You have won a free iPhone. Claim your reward now.', 'SPAM', 'ScamGuard Sample', 'SMS', 90),
('Congratulations! You have been selected for a lottery. Send your bank details.', 'SPAM', 'ScamGuard Sample', 'SMS', 98),
('Your debit card will be blocked unless you update your information.', 'SPAM', 'ScamGuard Sample', 'SMS', 94),
('Click here to receive your cash prize immediately.', 'SPAM', 'ScamGuard Sample', 'SMS', 91),
('Your account is suspended. Verify your password now.', 'SPAM', 'ScamGuard Sample', 'Email', 96),
('Send money now to complete your registration and get the job.', 'SPAM', 'ScamGuard Sample', 'SMS', 93),
('URGENT: Share your OTP to confirm your bank transaction.', 'SPAM', 'ScamGuard Sample', 'SMS', 99),
('Free reward waiting for you. Click the link to claim.', 'SPAM', 'ScamGuard Sample', 'SMS', 88),
('You have been selected for a work from home job. Pay registration fee.', 'SPAM', 'ScamGuard Sample', 'SMS', 94),
('Your credit card verification is required. Send your CVV.', 'SPAM', 'ScamGuard Sample', 'SMS', 99),
('Your OTP is 458921. Do not share it with anyone.', 'HAM', 'ScamGuard Sample', 'SMS', 5),
('Meeting is scheduled for tomorrow at 10 AM.', 'HAM', 'ScamGuard Sample', 'SMS', 2),
('Your electricity bill is due. Please check the official portal.', 'HAM', 'ScamGuard Sample', 'SMS', 10),
('Your order has been shipped and will arrive tomorrow.', 'HAM', 'ScamGuard Sample', 'SMS', 4),
('Please find the meeting details attached.', 'HAM', 'ScamGuard Sample', 'Email', 2),
('Your appointment is confirmed for Monday at 11 AM.', 'HAM', 'ScamGuard Sample', 'SMS', 2);
