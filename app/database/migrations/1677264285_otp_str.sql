PRAGMA foreign_keys;
PRAGMA foreign_keys = '0';
PRAGMA collation_list;
SAVEPOINT "db4s_edittable_1693768546781966695";
SAVEPOINT "db4s_renamecolumn_1693768553095609687";
PRAGMA database_list;
SELECT type,name,sql,tbl_name FROM "main".sqlite_master;
SAVEPOINT "RESTOREPOINT";
CREATE TABLE "sqlb_temp_table_1" (
	"id"	INTEGER UNIQUE,
	"login"	TEXT NOT NULL,
	"bind_token"	TEXT,
	"email2"	TEXT,
	"phone"	INT,
	"telegram"	INT,
	"otp"	TEXT,
	"reset_token"	INT,
	"bind_dest"	INTEGER DEFAULT 0,
	PRIMARY KEY("id" AUTOINCREMENT)
);
INSERT INTO "main"."sqlb_temp_table_1" ("bind_dest","bind_token","email2","id","login","otp","phone","reset_token","telegram") SELECT "bind_dest","bind_token","email2","id","login","otp","phone","reset_token","telegram" FROM "main"."users";
PRAGMA defer_foreign_keys;
PRAGMA defer_foreign_keys = '1';
DROP TABLE "main"."users";
ALTER TABLE "main"."sqlb_temp_table_1" RENAME TO "users";
PRAGMA defer_foreign_keys = '0';
RELEASE "db4s_renamecolumn_1693768553095609687";
PRAGMA database_list;
SELECT type,name,sql,tbl_name FROM "main".sqlite_master;
SELECT type,name,sql,tbl_name FROM sqlite_temp_master;
PRAGMA "main".foreign_key_check;
RELEASE "db4s_edittable_1693768546781966695";
PRAGMA foreign_keys = '1';
PRAGMA foreign_keys;
PRAGMA foreign_keys = '0';
PRAGMA collation_list;
SAVEPOINT "db4s_edittable_1693768560064931797";
ROLLBACK TO SAVEPOINT "db4s_edittable_1693768560064931797";
PRAGMA database_list;
SELECT type,name,sql,tbl_name FROM "main".sqlite_master;
SELECT type,name,sql,tbl_name FROM sqlite_temp_master;
RELEASE "db4s_edittable_1693768560064931797";
PRAGMA "main".foreign_key_check;
PRAGMA foreign_keys = '1';
