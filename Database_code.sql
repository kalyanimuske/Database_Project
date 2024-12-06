drop DATABASE CulturalFestivalPlanner3;

create DATABASE CulturalFestivalPlanner3;

USE CulturalFestivalPlanner3;

-- Create User table
CREATE TABLE User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    user_email VARCHAR(100) UNIQUE NOT NULL,
    address VARCHAR(255),
    user_contact VARCHAR(20),
    role ENUM('Sponsor', 'Organizer', 'Vendor', 'Volunteer', 'Participant', 'Attendee', 'Admin') NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Create Festival table
CREATE TABLE Festival (
    festival_id INT AUTO_INCREMENT PRIMARY KEY,
    festival_name VARCHAR(100) NOT NULL,
    festival_date DATE NOT NULL,
    fes_des TEXT
);

-- Create Venue table
CREATE TABLE Venue (
    venue_id INT AUTO_INCREMENT PRIMARY KEY,
    venue_name VARCHAR(100) NOT NULL,
    venue_location VARCHAR(255),
    venue_des TEXT
);

-- Create Event table
CREATE TABLE Event (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(100) NOT NULL,
    event_date DATE NOT NULL,
    event_feedback TEXT,
    event_starttime TIME,
    event_endtime TIME,
    ticket_price DECIMAL(10, 2) NOT NULL,
    festival_id INT,
    venue_id INT,
    FOREIGN KEY (festival_id) REFERENCES Festival(festival_id),
    FOREIGN KEY (venue_id) REFERENCES Venue(venue_id) ON DELETE CASCADE
);

-- Create Ticket table
CREATE TABLE Ticket (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_price DECIMAL(10, 2) NOT NULL,
    user_id INT,
    event_id INT,
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (event_id) REFERENCES Event(event_id)
);

-- Create Payment table
CREATE TABLE Payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(10, 2) NOT NULL,
    payment_date DATE NOT NULL,
    mode ENUM('Credit Card', 'Debit Card', 'PayPal', 'Apple Pay') NOT NULL,
    user_id INT,
    ticket_id INT UNIQUE,
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (ticket_id) REFERENCES Ticket(ticket_id)
);

-- Create Registration table
CREATE TABLE Registration (
    reg_id INT AUTO_INCREMENT PRIMARY KEY,
    reg_date DATE NOT NULL,
    user_id INT,
    event_id INT,
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (event_id) REFERENCES Event(event_id) ON DELETE CASCADE
);

-- Insert sample festivals
INSERT INTO Festival (festival_name, festival_date, fes_des)
VALUES
    ('Diwali', '2024-11-12', 'The festival of lights, celebrated with pooja and fireworks.'),
    ('Christmas', '2024-12-25', 'A holiday to celebrate the birth of Jesus Christ.'),
    ('Holi', '2025-03-06', 'A colorful festival celebrating the arrival of spring.');

-- Insert sample venues
INSERT INTO Venue (venue_name, venue_location, venue_des)
VALUES
    ('Main Hall', 'Atlanta Center', 'A spacious hall perfect for large gatherings.'),
    ('City Park', 'Downtown Atlanta', 'A beautiful park with open spaces for outdoor events.'),
    ('Community Center', 'Suburban Atlanta', 'A local center for community activities.'),
    ('Banquet Hall', 'Midtown Atlanta', 'An elegant banquet hall for formal events.'),
    ('Town Square', 'Old Town', 'A historic square perfect for parades.'),
    ('Open Grounds', 'Festival Road', 'Large open grounds for festivals and parties.');

-- Insert sample events
INSERT INTO Event (event_name, event_date, event_feedback, event_starttime, event_endtime, ticket_price, festival_id, venue_id)
VALUES
    ('Diwali Pooja', '2024-11-12', 'A sacred pooja to celebrate Diwali.', '18:00:00', '19:00:00', 10.00, 1, 1),
    ('Diwali Evening Light Party', '2024-11-12', 'A party to celebrate Diwali with lights and fireworks.', '20:00:00', '23:00:00', 15.00, 1, 2),
    ('Christmas Eve Dinner', '2024-12-24', 'A special dinner for Christmas Eve.', '19:00:00', '22:00:00', 20.00, 2, 3),
    ('Christmas Day Parade', '2024-12-25', 'A parade to celebrate Christmas.', '10:00:00', '12:00:00', 25.00, 2, 4),
    ('Holi Colors Party', '2025-03-06', 'Celebrate Holi with colors and music.', '14:00:00', '18:00:00', 5.00, 3, 5),
    ('Holi Bonfire', '2025-03-06', 'A bonfire celebration to mark Holi.', '19:00:00', '21:00:00', 8.00, 3, 6);

-- Insert sample users
INSERT INTO User (user_name, user_email, address, user_contact, role, password)
VALUES
    ('Admin User', 'admin@gmail.com', 'America', '1234567890', 'Admin', '$2b$12$j6wJdxERI.Pey43C2RWw6uas6sauye3Y0w7lPgcf/TNe9lpt3zAZC');

-- Query to verify data
SELECT e.event_name, e.event_date, v.venue_name, v.venue_location
FROM Event e
JOIN Venue v ON e.venue_id = v.venue_id;

-- Enable cascade deletes
ALTER TABLE Event
DROP FOREIGN KEY event_ibfk_2;
ALTER TABLE Event
ADD CONSTRAINT event_ibfk_2
FOREIGN KEY (venue_id) REFERENCES Venue (venue_id) ON DELETE CASCADE;

ALTER TABLE Registration
DROP FOREIGN KEY registration_ibfk_2;
ALTER TABLE Registration
ADD CONSTRAINT registration_ibfk_2
FOREIGN KEY (event_id) REFERENCES Event (event_id) ON DELETE CASCADE;



CREATE TABLE UserFestival (
    registration_id INT AUTO_INCREMENT PRIMARY KEY,  -- Unique identifier for each registration
    user_id INT NOT NULL,  -- Referencing User
    festival_id INT NOT NULL,  -- Referencing Festival
    role ENUM('Sponsor', 'Organizer', 'Vendor', 'Volunteer', 'Participant', 'Attendee') NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (festival_id) REFERENCES Festival(festival_id),
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP  -- To track when the registration occurred
);


CREATE TABLE UserEvent (
    registration_id INT AUTO_INCREMENT PRIMARY KEY,  -- Unique identifier for each registration
    user_id INT NOT NULL,  -- Referencing User
    event_id INT NOT NULL,  -- Referencing Event
    role ENUM('Sponsor', 'Organizer', 'Vendor', 'Volunteer', 'Participant', 'Attendee') NOT NULL,
    FOREIGN KEY (user_id) REFERENCES User(user_id),
    FOREIGN KEY (event_id) REFERENCES Event(event_id),
    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP  -- To track when the registration occurred
);

-- Insert more festivals
INSERT INTO Festival (festival_name, festival_date, fes_des)
VALUES
    ('Eid al-Fitr', '2025-04-10', 'A religious holiday marking the end of Ramadan, celebrated with prayers and feasts.'),
    ('Thanksgiving', '2024-11-28', 'A holiday to give thanks for the harvest and blessings of the past year.'),
    ('New Year', '2025-01-01', 'Celebration of the beginning of a new year with fireworks and parties.');


-- Insert more venues
INSERT INTO Venue (venue_name, venue_location, venue_des)
VALUES
    ('City Stadium', 'Downtown Atlanta', 'A large stadium perfect for outdoor sporting events and concerts.'),
    ('Beachside Pavilion', 'Coastal Georgia', 'A beautiful pavilion by the beach, ideal for sunset events.'),
    ('Convention Center', 'Midtown Atlanta', 'A modern convention center used for large events and conferences.'),
    ('Riverside Park', 'West Atlanta', 'A scenic park along the river, perfect for outdoor festivals and concerts.'),
    ('Mountain View Hall', 'North Georgia Mountains', 'An elegant hall with stunning views, perfect for formal events.');


-- Insert more events
INSERT INTO Event (event_name, event_date, event_feedback, event_starttime, event_endtime, ticket_price, festival_id, venue_id)
VALUES
    ('Eid Prayers', '2025-04-10', 'A spiritual prayer event for the community.', '08:00:00', '09:00:00', 0.00, 4, 1),
    ('Eid Feast', '2025-04-10', 'A feast to celebrate Eid with family and friends.', '12:00:00', '15:00:00', 15.00, 4, 3),
    ('Thanksgiving Parade', '2024-11-28', 'A grand parade celebrating Thanksgiving.', '09:00:00', '11:00:00', 10.00, 5, 2),
    ('Thanksgiving Dinner', '2024-11-28', 'A dinner gathering to celebrate Thanksgiving.', '18:00:00', '22:00:00', 20.00, 5, 3),
    ('New Year Countdown Party', '2024-12-31', 'A huge party to ring in the New Year with music and fireworks.', '22:00:00', '01:00:00', 30.00, 6, 4),
    ('New Year Fireworks Show', '2025-01-01', 'A grand fireworks show to celebrate the New Year.', '00:00:00', '00:30:00', 10.00, 6, 2)
   ;




select * from registration ;





