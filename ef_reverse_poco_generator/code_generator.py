import re
from jinja2 import Template

class CodeGenerator:
    def __init__(self, schema, namespace, dbcontext_name, naming_convention, configuration_style):
        self.schema = schema
        self.namespace = namespace
        self.dbcontext_name = dbcontext_name
        self.naming_convention = naming_convention
        self.configuration_style = configuration_style

    def generate(self):
        entities = self.generate_entities()
        dbcontext = self.generate_dbcontext()
        stored_procedures = self.generate_stored_procedures()
        return {
            'entities': entities,
            'dbcontext': dbcontext,
            'stored_procedures': stored_procedures
        }

    def generate_entities(self):
        entity_template = Template("""
using System;
using System.Collections.Generic;
{% if configuration_style == 'data_annotations' %}
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
{% endif %}

namespace {{ namespace }}
{
    {% if table_description %}
    /// <summary>
    /// {{ table_description | format_comment }}
    /// </summary>
    {% endif %}
    {% if configuration_style == 'data_annotations' %}[Table("{{ table_name }}")]{% endif %}
    public class {{ class_name }}
    {
        {% for column in columns %}
        {% if column.description %}
        /// <summary>
        /// {{ column.description | format_comment }}
        /// </summary>
        {% endif %}
        {% if configuration_style == 'data_annotations' %}
        {% if column.primary_key %}[Key]{% endif %}
        {% if column.primary_key and column.key_order is not none %}[Column(Order = {{ column.key_order }})]{% endif %}
        {% if not column.nullable %}[Required]{% endif %}
        [Column("{{ column.name }}")]
        {% endif %}
        public {{ column.csharp_type }} {{ column.property_name }} { get; set; }

        {% endfor %}
        {% for fk in foreign_keys %}
        {% if fk.description %}
        /// <summary>
        /// {{ fk.description | format_comment }}
        /// </summary>
        {% endif %}
        public virtual {{ fk.referenced_table }} {{ fk.property_name }} { get; set; }

        {% endfor %}
    }
}
""")

        def format_comment(comment):
            return re.sub(r'\s+', ' ', comment).strip()

        entity_template.environment.filters['format_comment'] = format_comment

        entities = {}
        for table_name, table_info in self.schema['tables'].items():
            class_name = self.format_name(table_name)
            columns = []
            primary_key_columns = table_info.get('primary_key', [])
            for column in table_info['columns']:
                column_info = {
                    'name': column['name'],
                    'property_name': self.format_name(column['name']),
                    'csharp_type': self.sql_to_csharp_type(column['type']),
                    'nullable': column['nullable'],
                    'primary_key': column['name'] in primary_key_columns,
                    'description': column.get('description', '')
                }
                if column_info['primary_key']:
                    column_info['key_order'] = primary_key_columns.index(column['name']) + 1 if len(primary_key_columns) > 1 else None
                columns.append(column_info)
            
            foreign_keys = []
            for fk in table_info.get('foreign_keys', []):
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
                table_description=table_info.get('description', ''),
                configuration_style=self.configuration_style
            )

        return entities

    def generate_dbcontext(self):
        dbcontext_template = Template("""
using System;
using System.Data.Entity;

namespace {{ namespace }}
{
    public class {{ dbcontext_name }} : DbContext
    {
        public {{ dbcontext_name }}(string nameOrConnectionString)
            : base(nameOrConnectionString)
        {
        }

        {% for table in tables %}
        public virtual DbSet<{{ table }}> {{ table }}s { get; set; }
        {% endfor %}

        protected override void OnModelCreating(DbModelBuilder modelBuilder)
        {
            {% if configuration_style == 'fluent_api' %}
            // Configure your model here using Fluent API
            {% for table_name, table_info in schema['tables'].items() %}
            modelBuilder.Entity<{{ format_name(table_name) }}>()
                .ToTable("{{ table_name }}");
            
            {% for column in table_info['columns'] %}
            modelBuilder.Entity<{{ format_name(table_name) }}>()
                .Property(e => e.{{ format_name(column['name']) }})
                .HasColumnName("{{ column['name'] }}")
                {% if column['name'] in table_info.get('primary_key', []) %}
                .HasDatabaseGeneratedOption(DatabaseGeneratedOption.Identity)
                .IsRequired();
                {% elif not column['nullable'] %}
                .IsRequired();
                {% endif %}
            
            {% endfor %}
            {% for fk in table_info.get('foreign_keys', []) %}
            modelBuilder.Entity<{{ format_name(table_name) }}>()
                .HasRequired(e => e.{{ format_name(fk['referenced_table']) }})
                .WithMany()
                .HasForeignKey(e => e.{{ format_name(fk['column']) }});
            
            {% endfor %}
            {% endfor %}
            {% endif %}
        }
    }
}
""")

        tables = [self.format_name(table) for table in self.schema['tables'].keys()]
        return dbcontext_template.render(
            namespace=self.namespace,
            dbcontext_name=self.dbcontext_name,
            tables=tables,
            schema=self.schema,
            format_name=self.format_name,
            configuration_style=self.configuration_style
        )

    def generate_stored_procedures(self):
        stored_procedure_template = Template("""
using System;
using System.Data.Entity;
using System.Data.SqlClient;
using System.Threading.Tasks;

namespace {{ namespace }}
{
    public partial class {{ dbcontext_name }}
    {
        {% for proc_name, proc_info in procedures.items() %}
        {% if proc_info.description %}
        /// <summary>
        /// {{ proc_info.description | format_comment }}
        /// </summary>
        {% endif %}
        public virtual async Task<int> {{ format_name(proc_name) }}Async({% for param in proc_info.parameters %}{{ param.csharp_type }} {{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %})
        {
            var parameters = new []
            {
                {% for param in proc_info.parameters %}
                new SqlParameter("{{ param.name }}", {{ param.name }}){% if not loop.last %},{% endif %}
                {% endfor %}
            };

            return await Database.ExecuteSqlCommandAsync("EXEC {{ proc_name }} {% for param in proc_info.parameters %}@{{ param.name }}{% if not loop.last %}, {% endif %}{% endfor %}", parameters);
        }

        {% endfor %}
    }
}
""")

        def format_comment(comment):
            return re.sub(r'\s+', ' ', comment).strip()

        stored_procedure_template.environment.filters['format_comment'] = format_comment

        return stored_procedure_template.render(
            namespace=self.namespace,
            dbcontext_name=self.dbcontext_name,
            procedures=self.schema['procedures'],
            format_name=self.format_name
        )

    def format_name(self, name):
        if self.naming_convention == 'camelcase':
            return ''.join(word.capitalize() for word in name.split('_'))
        else:
            return name

    def sql_to_csharp_type(self, sql_type):
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
            'decimal': 'decimal',
            'float': 'float',
            'double': 'double',
            'tinyint': 'byte',
            'smallint': 'short',
            'nvarchar': 'string',
            'varbinary': 'byte[]',
            'binary': 'byte[]',
            'image': 'byte[]',
            'money': 'decimal',
            'real': 'float',
            'smalldatetime': 'DateTime',
            'timestamp': 'byte[]',
            'uniqueidentifier': 'Guid'
        }
        return type_mapping.get(sql_type.lower(), 'object')