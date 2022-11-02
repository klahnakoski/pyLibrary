
## Some help for the programmer

Some nomenclature is required to help follow the logic of these modules


-----------------------------------

### Table

Same as with database terminology; it is a single, unordered, set of rows;

### Schema

A set of columns that describe all the (possibly optional) properties available on all rows of a table.

-----------------------------------

### Facts 

A set of records, and their relations, in a hierarchical database.  A collection of tables/relations limited to a hierarchy. An effective document store.

### Snowflake

Snowflake is the metadata on all columns, for all the tables, in the hierarchical database.

JSON Query Expressions are used to query hierarchical databases. The relations in a hierarchical database are limited to a tree; the path between any two tables is unique; in a query, no matter which table is "origin", any column in the hierarchical database can be accessed using a unique combination of joins with the origin.


-----------------------------------

### Container

Datastore that has multiple facts, equivalent to a relational database. 

### Namespace

Metadata for a container: Information on multiple snowflakes.

  