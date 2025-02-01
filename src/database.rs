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

    /// Creates a new table in the SQLite database by mapping some Python builtin types
    /// to SQLite types.
    fn create_table<'py>(&self, table_name: String, values: &Bound<'py, PyDict>) -> PyResult<()> {
        let conn = &self.connection.lock().map_err(|_| {
            PyRuntimeError::new_err("Failed to acquire database lock, another thread might use it.")
        })?;

        // We create the column definition that will be executed by the database engine.
        // We iter() through the PyDict sent by Python and check if the column
        // type is a valid python builtin type and is supported.
        // A type returns class "type" so we use its attribute "__name__"
        let column_definitions: Vec<String> = values
            .iter()
            .map(|(column_name, column_type)| {
                let column_type_name: String = column_type
                    .getattr("__name__")
                    .map_err(|_| {
                        PyRuntimeError::new_err(format!(
                            "Wrong type for the creation of the table \"{}\". Allowed types are valid Python builtin types: str, int, float, and bool.",
                            table_name
                        ))
                    })?
                    .extract()?;

                let sql_type_mapping = match column_type_name.as_str() {
                    "str" => "TEXT",
                    "int" => "INTEGER",
                    "float" => "REAL",
                    "bool" => "BOOLEAN",
                    _ => {
                        return Err(PyRuntimeError::new_err(format!(
                            "Wrong type for the creation of the table \"{}\". Allowed types are valid Python builtin types: str, int, float, and bool.",
                            table_name
                        )));
                    }
                };

                // Return the formatted column definition
                Ok(format!("{} {}", column_name, sql_type_mapping))
            })
            // After generating the string we collect it in the vector
            .collect::<PyResult<Vec<String>>>()?;

        let columns = column_definitions.join(", ");
        let sql = format!("CREATE TABLE IF NOT EXISTS {} ({})", table_name, columns);
        
        // Finally we execute the query to create the table if it doesn't exist.
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
