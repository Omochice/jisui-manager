DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS publishers; 
DROP TABLE IF EXISTS authors; 
DROP TABLE IF EXISTS categories;

CREATE TABLE books (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `title` TEXT NOT NULL,
    `isbn` TEXT,
    `publisher_id` INTEGER,
    `author_id` INTEGER,
    `category_id` INTEGER,
    `destination` TEXT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE publishers (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `name` TEXT NOT NULL
);

CREATE TABLE authors (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `name` TEXT NOT NULL
);

CREATE TABLE categories (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `name` TEXT NOT NULL
);
