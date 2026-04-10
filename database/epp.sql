BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "Detalle_Entrega" (
	"id_detalle"	INTEGER,
	"id_entrega"	INTEGER NOT NULL,
	"id_epp"	INTEGER NOT NULL,
	"cantidad"	INTEGER NOT NULL CHECK("cantidad" > 0),
	PRIMARY KEY("id_detalle" AUTOINCREMENT),
	FOREIGN KEY("id_entrega") REFERENCES "Entrega_EPP"("id_entrega"),
	FOREIGN KEY("id_epp") REFERENCES "Elemento_EPP"("id_epp")
);

CREATE TABLE IF NOT EXISTS "Elemento_EPP" (
	"id_epp"	INTEGER,
	"nombre_epp"	TEXT NOT NULL,
	"descripcion"	TEXT,
	"categoria"	TEXT,
	"talla"	TEXT,
	"estado"	TEXT NOT NULL,
	PRIMARY KEY("id_epp" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "Empleado" (
	"id_empleado"	INTEGER,
	"nombre"	TEXT NOT NULL,
	"apellido"	TEXT NOT NULL,
	"documento"	TEXT NOT NULL UNIQUE,
	"cargo"	TEXT,
	"area"	TEXT,
	"fecha_ingreso"	DATE,
	"estado"	TEXT NOT NULL,
	PRIMARY KEY("id_empleado" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "Entrega_EPP" (
	"id_entrega"	INTEGER,
	"id_empleado"	INTEGER NOT NULL,
	"id_usuario"	INTEGER NOT NULL,
	"fecha_entrega"	DATE NOT NULL,
	"observaciones"	TEXT,
	PRIMARY KEY("id_entrega" AUTOINCREMENT),
	FOREIGN KEY("id_empleado") REFERENCES "Empleado"("id_empleado"),
	FOREIGN KEY("id_usuario") REFERENCES "Usuario"("id_usuario")
);

CREATE TABLE IF NOT EXISTS "Inventario" (
	"id_inventario"	INTEGER,
	"id_epp"	INTEGER NOT NULL,
	"cantidad_disponible"	INTEGER NOT NULL CHECK("cantidad_disponible" >= 0),
	"fecha_actualizacion"	DATE,
	PRIMARY KEY("id_inventario" AUTOINCREMENT),
	FOREIGN KEY("id_epp") REFERENCES "Elemento_EPP"("id_epp")
);

CREATE TABLE IF NOT EXISTS "Usuario" (
	"id_usuario"	INTEGER,
	"nombre"	TEXT NOT NULL,
	"correo"	TEXT NOT NULL UNIQUE,
	"contrasena"	TEXT NOT NULL,
	"rol"	TEXT NOT NULL,
	"estado"	TEXT NOT NULL,
	PRIMARY KEY("id_usuario" AUTOINCREMENT)
);

COMMIT;
