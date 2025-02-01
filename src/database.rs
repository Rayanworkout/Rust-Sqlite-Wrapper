use std::sync::{Arc, Mutex};

use pyo3::{exceptions::PyRuntimeError, prelude::*, types::PyDict};
use rusqlite::Connection;

// https://doc.rust-lang.org/stable/book/
// https://pyo3.rs/v0.23.4/types.html

// We create the database class
#[pyclass]
struct Database {
    connection: Arc<Mutex<Connection>>, // Connection is async, it cannot be safely shared between Python threads.
                                        // That's why we use Arc<Mutex<Connection>> to enforce sync
}

#[pymethods]
impl Database {
    /// Method to instanciate a new database. We verify if path ends with the right extension
    /// and we return the Database object with its connection
    #[new]
    #[pyo3(signature = (db_path = None))] // Using signature here because we use the Option<> type
    fn new(db_path: Option<&str>) -> PyResult<Self> {
        let db_path = match db_path {
            Some(path) => path,
            None => "database.sqlite",
        };

        const ALLOWED_EXTENSIONS: [&str; 3] = [".sqlite", ".db", ".sql"];

        // If db_path does not end by one of the allowed extensions
        if !ALLOWED_EXTENSIONS
            .iter()
            .any(|ext| db_path.to_lowercase().ends_with(ext))
        {
            return Err(PyRuntimeError::new_err(format!(
                "\"db_path\" must end with one of the following extensions: {:?}.\n\"{}\" is not correct.",
                ALLOWED_EXTENSIONS.join(", "),
                db_path
            )));
        }

        // If for some reason we cannot open database, I map the SQLite
        // error into a PyRuntimeError
        let connection = Connection::open(db_path)
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to open DB: {}", e)))?;

        Ok(Database {
            connection: Arc::new(Mutex::new(connection)),
        })
    }

    /// Close the database connection
    fn close(&mut self) -> PyResult<()> {
        match Arc::get_mut(&mut self.connection) {
            Some(mutex) => {
                drop(mutex.lock().map_err(|_| {
                    PyRuntimeError::new_err(
                        "Failed to acquire database lock when closing the connection, another thread might use it.",
                    )
                })?);
                Ok(())
            }
            None => Err(PyRuntimeError::new_err(
                "Failed to close DB: active references exist.",
            )),
        }
    }

    fn create_table<'py>(&self, table_name: String, values: &Bound<'py, PyDict>) -> PyResult<()> {
        let conn = &self.connection.lock().map_err(|_| {
            PyRuntimeError::new_err("Failed to acquire database lock, another thread might use it.")
        })?;

        let mut column_definitions: Vec<String> = Vec::new();

        for (column_name, column_type) in values {
            // Ensure column_type is treated as a PyType and get its __name__
            let column_type_name: String = column_type.getattr("__name__")?.extract()?;

            let sql_type_mapping = match column_type_name.as_str() {
                "str" => "TEXT",
                "int" => "INTEGER",
                "float" => "REAL",
                "bool" => "BOOLEAN",
                _ => {
                    return Err(PyRuntimeError::new_err(
                        "Wrong type for table creation. Allowed types are valid python builtin types: str, int, float, bool.",
                    ))
                }
            };

            column_definitions.push(format!("{} {}", column_name, sql_type_mapping));
        }

        let columns = column_definitions.join(", ");
        let sql = format!("CREATE TABLE {} ({})", table_name, columns);

        conn.execute(&sql, [])
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to create table: {}", e)))?;
        
        Ok(())
    }

    // fn execute(&self, query: &str) -> PyResult<()> {
    //     let conn = self
    //         .conn
    //         .lock()
    //         .map_err(|_| PyRuntimeError::new_err("Failed to lock database"))?;
    //     conn.execute(query, [])
    //         .map_err(|e| PyRuntimeError::new_err(format!("Query failed: {}", e)))?;
    //     Ok(())
    // }
}

#[pymodule]
fn rust_sqlite_wrapper(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Database>()?;
    Ok(())
}
