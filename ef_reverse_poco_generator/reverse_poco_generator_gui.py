# reverse_poco_generator_gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import os

from connection_history import ConnectionHistory
from db_connector import connect
from schema_reader import read_schema
from code_generator import CodeGenerator

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ReversePocoGeneratorGUI:
    def __init__(self, master):
        self.master = master
        master.title("EF Reverse POCO Generator")
        self.history = ConnectionHistory()

        # Database Type
        ttk.Label(master, text="Database Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.db_type = ttk.Combobox(master, values=["mysql", "postgresql", "sqlserver", "sqlite"])
        self.db_type.grid(row=0, column=1, padx=5, pady=5)

        # Host
        ttk.Label(master, text="Host:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.host = ttk.Entry(master)
        self.host.grid(row=1, column=1, padx=5, pady=5)

        # Port
        ttk.Label(master, text="Port:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.port = ttk.Entry(master)
        self.port.grid(row=2, column=1, padx=5, pady=5)

        # Username
        ttk.Label(master, text="Username:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.username = ttk.Entry(master)
        self.username.grid(row=3, column=1, padx=5, pady=5)

        # Password
        ttk.Label(master, text="Password:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.password = ttk.Entry(master, show="*")
        self.password.grid(row=4, column=1, padx=5, pady=5)

        # Database
        ttk.Label(master, text="Database:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.database = ttk.Entry(master)
        self.database.grid(row=5, column=1, padx=5, pady=5)

        # History Dropdown
        ttk.Label(master, text="Connection History:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.history_var = tk.StringVar()
        self.history_dropdown = ttk.Combobox(master, textvariable=self.history_var)
        self.history_dropdown.grid(row=6, column=1, padx=5, pady=5)
        self.history_dropdown.bind("<<ComboboxSelected>>", self.load_history_item)
        self.update_history_dropdown()

        # Namespace
        ttk.Label(master, text="Namespace:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=5)
        self.namespace = ttk.Entry(master)
        self.namespace.grid(row=7, column=1, padx=5, pady=5)

        # DbContext Name
        ttk.Label(master, text="DbContext Name:").grid(row=8, column=0, sticky=tk.W, padx=5, pady=5)
        self.dbcontext_name = ttk.Entry(master)
        self.dbcontext_name.grid(row=8, column=1, padx=5, pady=5)

        # Naming Convention
        ttk.Label(master, text="Naming Convention:").grid(row=9, column=0, sticky=tk.W, padx=5, pady=5)
        self.naming_convention = tk.StringVar(value="camelcase")
        self.camelcase_radio = ttk.Radiobutton(master, text="CamelCase", variable=self.naming_convention, value="camelcase")
        self.camelcase_radio.grid(row=9, column=1, sticky=tk.W, padx=5, pady=2)
        self.original_radio = ttk.Radiobutton(master, text="Original", variable=self.naming_convention, value="original")
        self.original_radio.grid(row=10, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Configuration Style
        ttk.Label(master, text="Configuration Style:").grid(row=11, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_style = tk.StringVar(value="data_annotations")
        self.data_annotations_radio = ttk.Radiobutton(master, text="Data Annotations", variable=self.config_style, value="data_annotations")
        self.data_annotations_radio.grid(row=11, column=1, sticky=tk.W, padx=5, pady=2)
        self.fluent_api_radio = ttk.Radiobutton(master, text="Fluent API", variable=self.config_style, value="fluent_api")
        self.fluent_api_radio.grid(row=12, column=1, sticky=tk.W, padx=5, pady=2)

        # Generate Button
        self.generate_button = ttk.Button(master, text="Generate", command=self.generate_code)
        self.generate_button.grid(row=13, column=0, columnspan=2, pady=10)

    def update_history_dropdown(self):
        history = self.history.get_history()
        self.history_dropdown['values'] = [f"{item['db_type']} - {item['database']} on {item['host']}" for item in history]

    def load_history_item(self, event):
        selected_index = self.history_dropdown.current()
        if selected_index >= 0:
            selected_item = self.history.get_history()[selected_index]
            self.db_type.set(selected_item['db_type'])
            self.host.delete(0, tk.END)
            self.host.insert(0, selected_item['host'])
            self.port.delete(0, tk.END)
            self.port.insert(0, selected_item['port'])
            self.username.delete(0, tk.END)
            self.username.insert(0, selected_item['user'])
            self.password.delete(0, tk.END)
            self.password.insert(0, selected_item['password'])
            self.database.delete(0, tk.END)
            self.database.insert(0, selected_item['database'])

    def generate_code(self):
        try:
            db_type = self.db_type.get()
            host = self.host.get()
            port = self.port.get()
            username = self.username.get()
            password = self.password.get()
            database = self.database.get()
            namespace = self.namespace.get()
            dbcontext_name = self.dbcontext_name.get()
            naming_convention = self.naming_convention.get()
            configuration_style = self.config_style.get()

            # Validate input
            if not all([db_type, host, port, username, password, database, namespace, dbcontext_name]):
                raise ValueError("All fields must be filled")

            # Connect to database
            conn_params = {
                'db_type': db_type,
                'host': host,
                'port': int(port),
                'user': username,
                'password': password,
                'database': database
            }
            logger.debug(f"Attempting to connect with parameters: {conn_params}")
            db = connect(conn_params)
            logger.info("Database connection successful")

            # Add successful connection to history
            try:
                self.history.add_connection(conn_params)
                self.update_history_dropdown()
            except Exception as e:
                logger.warning(f"Failed to add connection to history: {str(e)}")

            # Read schema
            logger.debug("Attempting to read database schema")
            schema = read_schema(db, naming_convention)
            logger.info("Schema read successfully")

            # Generate code
            logger.debug("Generating code")
            code_generator = CodeGenerator(schema, namespace, dbcontext_name, naming_convention, configuration_style)
            generated_code = code_generator.generate()
            logger.info("Code generated successfully")

            # Create a directory to save the generated files
            directory = filedialog.askdirectory(title="Select Directory to Save Generated Files")
            if not directory:
                logger.warning("Code generation cancelled by user")
                messagebox.showwarning("Cancelled", "Code generation was cancelled")
                return

            # Save each class to a separate file
            for class_name, code in generated_code['entities'].items():
                file_path = os.path.join(directory, f"{class_name}.cs")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                logger.info(f"Entity class {class_name} saved to {file_path}")

            # Save DbContext to a separate file
            dbcontext_file_path = os.path.join(directory, f"{dbcontext_name}.cs")
            with open(dbcontext_file_path, 'w', encoding='utf-8') as f:
                f.write(generated_code['dbcontext'])
            logger.info(f"DbContext saved to {dbcontext_file_path}")

            # Save stored procedures to a separate file
            stored_procedures_file_path = os.path.join(directory, f"{dbcontext_name}StoredProcedures.cs")
            with open(stored_procedures_file_path, 'w', encoding='utf-8') as f:
                f.write(generated_code['stored_procedures'])
            logger.info(f"Stored procedures saved to {stored_procedures_file_path}")

            messagebox.showinfo("Success", f"Code generated successfully and saved to {directory}")

        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            messagebox.showerror("Validation Error", str(e))
        except ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            messagebox.showerror("Connection Error", str(e))
        except Exception as e:
            logger.exception("An unexpected error occurred:")
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")