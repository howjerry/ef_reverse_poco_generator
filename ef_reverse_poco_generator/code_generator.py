# code_generator.py
from jinja2 import Template

class CodeGenerator:
    def __init__(self, schema, namespace, dbcontext_name, naming_convention):
        self.schema = schema
        self.namespace = namespace
        self.dbcontext_name = dbcontext_name
        self.naming_convention = naming_convention

    def generate(self):
        entities = self.generate_entities()
        dbcontext = self.generate_dbcontext()
        return {
            'entities': entities,
            'dbcontext': dbcontext
        }

    def generate_entities(self):
        entity_template = Template("""
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace {{ namespace }}
{
    {% if table_description %}
    /// <summary>
    /// {{ table_description }}
    /// </summary>
    {% endif %}
    [Table("{{ table_name }}")]
    public class {{ class_name }}
    {
        {% for column in columns %}
        {% if column.description %}
        /// <summary>
        /// {{ column.description }}
        /// </summary>
        {% endif %}
        {% if column.primary_key %}[Key]{% endif %}
        {% if not column.nullable %}[Required]{% endif %}
        [Column("{{ column.name }}")]
        public {{ column.csharp_type }} {{ column.property_name }} { get; set; }

        {% endfor %}
        {% for fk in foreign_keys %}
        {% if fk.description %}
        /// <summary>
        /// {{ fk.description }}
        /// </summary>
        {% endif %}
        public virtual {{ fk.referenced_table }} {{ fk.property_name }} { get; set; }

        {% endfor %}
    }
}
""")

        entities = {}
        for table_name, table_info in self.schema['tables'].items():
            class_name = self.format_name(table_name)
            columns = []
            for column in table_info['columns']:
                columns.append({
                    'name': column['name'],
                    'property_name': self.format_name(column['name']),
                    'csharp_type': self.sql_to_csharp_type(column['type']),
                    'nullable': column['nullable'],
                    'primary_key': column['primary_key'],
                    'description': column.get('description', '')
                })
            
            foreign_keys = []
            for fk in table_info['foreign_keys']:
                foreign_keys.append({
                    'referenced_table': self.format_name(fk['referenced_table']),
                    'property_name': self.format_name(fk['referenced_table']),
                    'description': fk.get('description', '')
                })

            entities[class_name] = entity_template.render(
                namespace=self.namespace,
                table_name=table_name,
                class_name=class_name,
                columns=columns,
                foreign_keys=foreign_keys,
                table_description=table_info.get('description', '')
            )

        return entities

    def generate_dbcontext(self):
        dbcontext_template = Template("""
using System;
using System.Data.Entity;

namespace {{ namespace }}
{
    /// <summary>
    /// Represents the database context for the application.
    /// </summary>
    public class {{ dbcontext_name }} : DbContext
    {
        /// <summary>
        /// Initializes a new instance of the <see cref="{{ dbcontext_name }}"/> class.
        /// </summary>
        /// <param name="nameOrConnectionString">The name of the connection string or the connection string itself.</param>
        public {{ dbcontext_name }}(string nameOrConnectionString)
            : base(nameOrConnectionString)
        {
        }

        {% for table in tables %}
        /// <summary>
        /// Gets or sets the <see cref="{{ table }}"/> entities.
        /// </summary>
        public virtual DbSet<{{ table }}> {{ table }}s { get; set; }

        {% endfor %}
        /// <summary>
        /// Configures the model that was discovered by convention from the entity types.
        /// </summary>
        /// <param name="modelBuilder">The builder being used to construct the model for this context.</param>
        protected override void OnModelCreating(DbModelBuilder modelBuilder)
        {
            // Configure your model here
        }
    }
}
""")

        tables = [self.format_name(table) for table in self.schema['tables'].keys()]
        return dbcontext_template.render(
            namespace=self.namespace,
            dbcontext_name=self.dbcontext_name,
            tables=tables
        )

    def format_name(self, name):
        if self.naming_convention == 'camelcase':
            return ''.join(word.capitalize() for word in name.split('_'))
        else:
            return name

    @staticmethod
    def sql_to_csharp_type(sql_type):
        type_mapping = {
            'int': 'int',
            'bigint': 'long',
            'varchar': 'string',
            'char': 'string',
            'text': 'string',
            'datetime': 'DateTime',
            'date': 'DateTime',
            'time': 'TimeSpan',
            'bit': 'bool',
            'bool': 'bool',
            'boolean': 'bool',
            'decimal': 'decimal',
            'float': 'float',
            'double': 'double'
        }
        return type_mapping.get(sql_type.lower(), 'object')

def generate(schema, namespace, dbcontext_name, naming_convention):
    generator = CodeGenerator(schema, namespace, dbcontext_name, naming_convention)
    return generator.generate()