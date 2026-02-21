USE fleetflow;
-- Update the allowed statuses for Drivers
ALTER TABLE Drivers MODIFY status ENUM('Available', 'On Trip', 'Off Duty', 'Suspended') DEFAULT 'Available';

-- Set all currently active drivers to 'Available' so the dispatcher can see them
UPDATE Drivers SET status = 'Available' WHERE status = 'On Duty';

USE fleetflow;
-- Update the allowed statuses for Drivers
ALTER TABLE Drivers MODIFY status ENUM('Available', 'On Trip', 'Off Duty', 'Suspended') DEFAULT 'Available';

-- Set all currently active drivers to 'Available' so the dispatcher can see them
UPDATE Drivers SET status = 'Available' WHERE status = 'On Duty';

USE fleetflow;

-- 1. Upgrade Drivers Table for Safety Officers
ALTER TABLE Drivers ADD COLUMN license_expiry DATE;
ALTER TABLE Drivers ADD COLUMN safety_score INT DEFAULT 100;

-- 2. Upgrade Vehicles Table for Financial Analysts
ALTER TABLE Vehicles ADD COLUMN odometer INT DEFAULT 0;
ALTER TABLE Vehicles ADD COLUMN acquisition_cost DECIMAL(10,2) DEFAULT 50000.00;
ALTER TABLE Vehicles ADD COLUMN revenue_generated DECIMAL(10,2) DEFAULT 150000.00;

-- 3. Create the Fuel Logs Table
CREATE TABLE IF NOT EXISTS FuelLogs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT,
    liters DECIMAL(10,2),
    cost DECIMAL(10,2),
    log_date DATE,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicles(id)
);

-- 4. Add the user accounts so you can test them!
INSERT IGNORE INTO Users (email, password_hash, role) VALUES ('safety@fleetflow.com', 'hackathon123', 'Safety Officer');
INSERT IGNORE INTO Users (email, password_hash, role) VALUES ('finance@fleetflow.com', 'hackathon123', 'Financial Analyst');

USE fleetflow;

-- 1. Temporarily turn off Safe Update Mode
SET SQL_SAFE_UPDATES = 0;

-- 2. Update the drivers to 'Available' so the Dispatcher can see them
UPDATE Drivers SET status = 'Available' WHERE status = 'On Duty';

-- 3. Turn Safe Update Mode back on to keep things secure
SET SQL_SAFE_UPDATES = 1;

SELECT * FROM Users;
USE fleetflow;
INSERT IGNORE INTO Users (email, password_hash, role) VALUES ('safety@fleetflow.com', 'hackathon123', 'Safety Officer');
INSERT IGNORE INTO Users (email, password_hash, role) VALUES ('finance@fleetflow.com', 'hackathon123', 'Financial Analyst');

USE fleetflow;
-- Force update roles to match the exact strings used in your HTML dropdown
UPDATE Users SET role = 'Safety Officer' WHERE email = 'safety@fleetflow.com';
UPDATE Users SET role = 'Financial Analyst' WHERE email = 'finance@fleetflow.com';

-- Verify the data
SELECT email, role FROM Users;

CREATE TABLE FuelLogs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id INT NOT NULL,
    liters DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2) NOT NULL,
    log_date DATE NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES Vehicles(id) 
    ON DELETE CASCADE
);