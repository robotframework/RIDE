CREATE TABLE libraries (id INTEGER PRIMARY KEY,
                        name TEXT,
                        arguments TEXT,
                        last_updated REAL);

CREATE TABLE keywords (name TEXT,
                       doc TEXT,
                       arguments TEXT,
                       library INTEGER,
                       FOREIGN KEY(library) REFERENCES libraries(id));
