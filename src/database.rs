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
    fn new(db_path: &str) -> PyResult<Self> {
        let conn = Connection::open(db_path).map_err(|e| {
            pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to open DB: {}", e))
        })?;

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
