-- SISTEMA DE INVENTARIO NUP-Leonardo Rojas Varela
-- Base de datos: PostgreSQL

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL CHECK (rol IN ('administrador', 'vendedor')),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE proveedores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    contacto VARCHAR(100),
    telefono VARCHAR(20),
    email VARCHAR(100)
);

CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('NUP', 'NUP Pets')),
    categoria_id INTEGER REFERENCES categorias(id),
    proveedor_id INTEGER REFERENCES proveedores(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lotes (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    numero_lote VARCHAR(50) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    cantidad_inicial INTEGER NOT NULL CHECK (cantidad_inicial >= 0),
    stock_actual INTEGER NOT NULL CHECK (stock_actual >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(producto_id, numero_lote)
);

CREATE TABLE movimientos (
    id SERIAL PRIMARY KEY,
    lote_id INTEGER NOT NULL REFERENCES lotes(id),
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('entrada', 'salida', 'reposicion')),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    vendedor_id INTEGER NOT NULL REFERENCES usuarios(id),
    comentario TEXT,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bitacora_seguridad (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id),
    accion VARCHAR(100) NOT NULL,
    ip VARCHAR(45),
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDICES
CREATE INDEX idx_lotes_producto ON lotes(producto_id);
CREATE INDEX idx_lotes_vencimiento ON lotes(fecha_vencimiento);
CREATE INDEX idx_movimientos_lote ON movimientos(lote_id);
CREATE INDEX idx_movimientos_fecha ON movimientos(fecha_hora);

-- DATOS INICIALES (usar despues, cuando la app genere hash)
INSERT INTO categorias (nombre) VALUES ('Shampoo'), ('Acondicionador'), ('Crema'), ('Maquillaje'), ('Accesorios'), ('Pets');

INSERT INTO proveedores (nombre, contacto, telefono, email) VALUES 
('Laboratorios NUP', 'Juan Pérez', '+56912345678', 'ventas@nup.cl'),
('Distribuidora Pet', 'María López', '+56987654321', 'contacto@distpet.cl');

INSERT INTO productos (nombre, sku, tipo, categoria_id, proveedor_id) VALUES 
('Shampoo Forte', 'NUP-001', 'NUP', 1, 1),
('Acondicionador Reparador', 'NUP-002', 'NUP', 2, 1),
('Shampoo Pets', 'PET-001', 'NUP Pets', 6, 2);

INSERT INTO lotes (producto_id, numero_lote, fecha_vencimiento, cantidad_inicial, stock_actual) VALUES 
(1, 'LOTE001', '2026-12-31', 100, 100),
(2, 'LOTE002', '2026-12-31', 50, 50),
(3, 'LOTE003', '2026-10-31', 80, 80);