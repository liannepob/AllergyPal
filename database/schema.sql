-- users table translates to allergies, user_allergies, restaurants, saved_restaurants, friends, password_resets
-- friends table relates to users table, and vice versa
-- enforcing: unique email/severity

-- USERS table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    hometown TEXT NOT NULL,
    food_pref TEXT NOT NULL,
    created_at DATE NOT NULL
);

-- ALLERGIES table
CREATE TABLE allergies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT
);

-- USER_ALLERGIES table joined
CREATE TABLE user_allergies (
    user_id INTEGER NOT NULL,
    allergy_id INTEGER NOT NULL,
    severity TEXT NOT NULL,
    notes TEXT,
    PRIMARY KEY (user_id, allergy_id), -- user_id and allergy_id is how this table is referenced
    FOREIGN KEY (user_id) REFERENCES users(id), -- user_id must match real user.id in users
    FOREIGN KEY (allergy_id) REFERENCES allergies(id) -- allergy_id must reference an allergy in the allergies table with an ID
);

-- RESTAURANTS table
CREATE TABLE restaurants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT, -- going to be an api from google or yelp
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    lat REAL,
    lng REAL
);

-- SAVED RESTAURANTS table joined
CREATE TABLE saved_restaurants (
    user_id INTEGER NOT NULL,
    restaurant_id INTEGER NOT NULL,
    status TEXT NOT NULL, -- ("unsafe"/"safe"/"unsure"),
    notes TEXT,
    created_at DATE NOT NULL,
    PRIMARY KEY (user_id, restaurant_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id)
);

-- FRIENDS table
CREATE TABLE friends (
    requester_id INTEGER NOT NULL, -- gets from user_id
    addressee_id INTEGER NOT NULL,-- gets from user_id
    status TEXT NOT NULL, -- (pending/accepted/blocked)
    created_at DATE NOT NULL,
    PRIMARY KEY (requester_id, addressee_id),
    FOREIGN KEY (requester_id) REFERENCES users(id),
    FOREIGN KEY (addressee_id) REFERENCES users(id)
);

-- PASSWORD_RESETS table
CREATE TABLE password_resets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL, -- the text used to email a user through an API
    expires_at DATE NOT NULL, -- used for an OTP
    used_at DATE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE emergency_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    contact_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    age INTEGER,
    email TEXT,
    address TEXT,
    relationship TEXT,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- new things learned PK/FK
-- PK = primary key, ID of a row no 2 users can have the same primary key
-- FK = foreign key, referenced key from another table, depends on another PK
