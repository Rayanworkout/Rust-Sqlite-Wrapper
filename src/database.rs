use std::sync::{Arc, Mutex};

use pyo3::{exceptions::PyRuntimeError, prelude::*};
use rusqlite::Connection;

// We create the database class
#[pyclass]
struct Database {
    conn: Arc<Mutex<Connection>>, // Connection async, it cannot be safely shared between Python threads.
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

        // Checking file extension
        const ALLOWED_EXTENSIONS: [&str; 2] = [".sqlite", ".db"];

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
        let conn = Connection::open(db_path)
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to open DB: {}", e)))?;

        Ok(Database {
            conn: Arc::new(Mutex::new(conn)),
        })
    }

    fn execute(&self, query: &str) -> PyResult<()> {
        let conn = self
            .conn
            .lock()
            .map_err(|_| PyRuntimeError::new_err("Failed to lock database"))?;
        conn.execute(query, [])
            .map_err(|e| PyRuntimeError::new_err(format!("Query failed: {}", e)))?;
        Ok(())
    }
}

#[pymodule]
fn rust_sqlite_wrapper(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Database>()?;
    Ok(())
}
