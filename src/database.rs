use std::sync::{Arc, Mutex};

use pyo3::{
    exceptions::PyRuntimeError,
    prelude::*,
    types::{PyBool, PyDict, PyFloat, PyInt, PyList, PyString, PyTuple},
};
use rusqlite::{params_from_iter, Connection, ToSql};

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
    fn create_table<'py>(
        &self,
        table_name: String,
        dict_columns: &Bound<'py, PyDict>,
    ) -> PyResult<usize> {
        // We create the column definition that will be executed by the database engine.
        // We iter() through the PyDict sent by Python and check if the column
        // type is a valid python builtin type and is supported.
        // A type returns class "type" so we use its attribute "__name__"

        let table_name_lowercase = table_name.to_lowercase();
        let column_definitions: Vec<String> = dict_columns
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
        let sql = format!(
            "CREATE TABLE IF NOT EXISTS {} ({})",
            table_name_lowercase, columns
        );

        // Finally we execute the query to create the table if it doesn't exist.
        Ok(self
            .connection
            .lock()
            .map_err(|_| {
                PyRuntimeError::new_err(
                    "Failed to acquire database lock, another thread might use it.",
                )
            })?
            .execute(&sql, [])
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to create table: {}", e)))?)
    }

    /// Insert a record in a specific table
    // fn insert<'py>(&self, table_name: String, value: &Bound<'py, PyAny>) -> PyResult<()> {
    //     let query = format!("INSERT INTO {} VALUES {}", table_name, value)
    //     &self.execute(query);
    //     Ok(())
    // }

    /// Executes a SQL query with the given parameters.
    ///
    /// # Arguments
    /// * `query` - The SQL query string to execute
    /// * `params` - A Python list or tuple containing query parameters
    ///
    /// # Returns
    /// * `PyResult<()>` - Ok(()) on successful execution, or Err with a PyRuntimeError
    ///
    /// # Supported Parameter Types
    /// * Integer (i64)
    /// * Float (f64)
    /// * String
    /// * Boolean
    ///
    /// # Examples
    /// ```python
    /// db.execute("INSERT INTO users (name, age) VALUES (?, ?)", ["John", 30])
    /// db.execute("UPDATE users SET active = ? WHERE id = ?", (True, 1))
    /// ```
    fn execute<'py>(&self, query: &str, params: &Bound<'py, PyAny>) -> PyResult<usize> {

        // Convert Python list/tuple to Vec of PyAny
        let params: Vec<Bound<'_, PyAny>> = match params.get_type().name()?.to_str()? {
            "list" => params.downcast::<PyList>()?.iter().collect::<Vec<_>>(),
            "tuple" => params.downcast::<PyTuple>()?.iter().collect::<Vec<_>>(),
            _ => {
                return Err(PyRuntimeError::new_err(
                    "Unsupported parameter type. Expected a list or tuple.",
                ));
            }
        };

        // Convert all parameters to SQL-compatible types
        // Box<T> is a smart pointer that puts data on the heap rather than the stack.
        //We need it here because:

        // - Different parameter types have different sizes (String vs i64)
        // - We need to store them in a Vec together

        // dyn is used for dynamic dispatch with traits. In our case:

        // ToSql is a trait implemented by various types (String, i64, etc.)
        // dyn ToSql means "any type that implements ToSql"
        // We need Box<dyn ToSql> to store different types that implement ToSql in our Vec
        let sql_params: Vec<Box<dyn ToSql>> = params
            .iter() // Iterate over Python parameters
            .map(|item| -> PyResult<Box<dyn ToSql>> {
                // For each parameter, try to convert it to a SQL type:
                if item.is_instance_of::<PyInt>() {
                    // Python int -> Rust i64 -> Box<dyn ToSql>
                    Ok(Box::new(item.extract::<i64>()?))
                } else if item.is_instance_of::<PyFloat>() {
                    // Python float -> Rust f64 -> Box<dyn ToSql>
                    Ok(Box::new(item.extract::<f64>()?))
                } else if item.is_instance_of::<PyString>() {
                    // Python str -> Rust String -> Box<dyn ToSql>
                    Ok(Box::new(item.extract::<String>()?))
                } else if item.is_instance_of::<PyBool>() {
                    // Python bool -> Rust bool -> Box<dyn ToSql>
                    Ok(Box::new(item.extract::<bool>()?))
                } else {
                    // Unsupported type -> PyErr
                    Err(PyRuntimeError::new_err(
                        "Unsupported parameter type in query.",
                    ))
                }
            })
            .collect::<PyResult<Vec<_>>>()?; // Collect into Result<Vec<Box<dyn ToSql>>>
                                             // Final ? operator unwraps the PyResult

        // Execute the query with thread-safe connection handling
        // and return the result
        Ok(self
            .connection
            .lock()
            .map_err(|_| {
                PyRuntimeError::new_err(
                    "Failed to acquire database lock, another thread might use it.",
                )
            })?
            .execute(query, params_from_iter(sql_params.iter()))
            .map_err(|e| PyRuntimeError::new_err(format!("Failed to execute query: {}", e)))?)
    }
}

#[pymodule]
fn rust_sqlite_wrapper(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Database>()?;
    Ok(())
}
