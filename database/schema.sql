PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER  PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT     NOT NULL,
    carrera       TEXT     NOT NULL,
    semestre      INTEGER  NOT NULL CHECK (semestre BETWEEN 1 AND 15),
    creado_en     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id  INTEGER  PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER  NOT NULL,
    nombre      TEXT     NOT NULL,
    activa      INTEGER  NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id       INTEGER  PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER  NOT NULL,
    titulo        TEXT     NOT NULL,
    materia       TEXT,
    fecha_limite  DATE,
    prioridad     TEXT     DEFAULT 'media' CHECK (prioridad IN ('alta','media','baja')),
    estado        TEXT     DEFAULT 'pendiente' CHECK (estado IN ('pendiente','completada')),
    creada_en     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    msg_id      INTEGER  PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER  NOT NULL,
    rol         TEXT     NOT NULL CHECK (rol IN ('user','assistant')),
    contenido   TEXT     NOT NULL,
    timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);